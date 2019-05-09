odoo.define('voip.user_agent', function (require) {
"use strict";

var ajax = require('web.ajax');
var Class = require('web.Class');
var core = require('web.core');
var Dialog = require('web.Dialog');
var mixins = require('web.mixins');
var ServicesMixin = require('web.ServicesMixin');

var _t = core._t;

var clean_number = function(number) {
    return number.replace(/[\s-/.\u00AD]/g, '');
};

var CALL_STATE = {
    NO_CALL: 0,
    RINGING_CALL: 1,
    ONGOING_CALL: 2,
};

var UserAgent = Class.extend(mixins.EventDispatcherMixin, ServicesMixin, {
    /**
     * @constructor
     */
    init: function (parent) {
        mixins.EventDispatcherMixin.init.call(this);
        this.setParent(parent);
        this.callState = CALL_STATE.NO_CALL;
        ajax.rpc('/web/dataset/call_kw/voip.configurator/get_pbx_config', {
            model: 'voip.configurator',
            method: 'get_pbx_config',
            args: [],
            kwargs: {},
        }).then(this._initUa.bind(this));
        this.blocked = false;
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * Hangs up the current call.
     */
    hangup: function () {
        if (this.mode === "demo") {
            if (this.callState === CALL_STATE.ONGOING_CALL) {
                this._onBye();
            } else {
                this._onCancel();
            }
        }
        if (this.callState !== CALL_STATE.NO_CALL) {
            if (this.callState === CALL_STATE.RINGING_CALL) {
                try {
                    this.sipSession.cancel();
                } catch (err) {
                    console.error('Cancel failed:', err);
                }
            } else {
                this.sipSession.bye();
            }
        }
    },
    /**
     * Instantiates a new sip call.
     *
     * @param {string} number
     */
    makeCall: function (number) {
        this.ringbacktone.play();
        if (this.mode === "demo") {
            var self = this;
            this.timerAccepted = setTimeout(function () {
                self._onAccepted();
            },3000);
            return;
        }
        this._makeCall(number);
    },
    /**
     * Mutes the current call
     */
    muteCall: function () {
        if (this.callState === CALL_STATE.ONGOING_CALL) {
            this._toggleMute(true);
        }
    },
    /**
     * Sends dtmf, when there is a click on keypad number.
     *
     * @param {string} number number clicked
     */
    sendDtmf: function (number) {
        if (this.callState === CALL_STATE.ONGOING_CALL) {
            this.sipSession.dtmf(number);
        }
    },
    /**
     * Transfers the call to the given number.
     *
     * @param {string} number
     */
    transfer: function (number) {
        if (this.callState === CALL_STATE.ONGOING_CALL) {
            this.sipSession.refer(number);
        }
    },
    /**
     * Unmutes the current call
     */
    unmuteCall: function () {
       if (this.callState === CALL_STATE.ONGOING_CALL) {
            this._toggleMute(false);
        }
    },
    /**
     * Returns PBX Configuration.
     *
     * @return {Object} result user and pbx configuration return by the rpc
     */
    getPbxConfiguration: function() {
        return this.infoPbxConfiguration;
    },
    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Answer to a INVITE message and accept the call.
     *
     * @private
     * @param {SIP.Session} inviteSession invite SIP session to answer
     * @param {Object} params Params for the incomming call
     */
    _answerCall: function (inviteSession, incomingCallParams) {
        this.incomingtone.pause();
        if (this.callState === CALL_STATE.ONGOING_CALL) {
            this.hangup();
        }
        var callOptions = {
            sessionDescriptionHandlerOptions: {
                constraints: {
                    audio: true,
                    video: false
                }
            }
        };
        inviteSession.accept(callOptions);
        this.incomingCall = true;
        this.sipSession = inviteSession;
        this.callState = CALL_STATE.ONGOING_CALL;
        this._configureRemoteAudio();
        this.sipSession.sessionDescriptionHandler.on('addTrack',_.bind(this._configureRemoteAudio,this));
        this.trigger_up('sip_incoming_call', incomingCallParams);
        //Bind action when the call is hanged up
        this.sipSession.on('bye', _.bind(this._onBye, this));
    },
    /**
     * Clean the audio media stream after a call.
     *
     * @private
     */
    _cleanRemoteAudio: function () {
        this.$remoteAudio.srcObject = null;
        this.$remoteAudio.pause();
    },
    /**
     * Configure the remote audio, the ringtones
     *
     * @private
     */
    _configureDomElements: function () {
        this.$remoteAudio = document.createElement("audio");
        this.$remoteAudio.autoplay = true;
        $("html").append(this.$remoteAudio);
        this.ringbacktone = document.createElement("audio");
        this.ringbacktone.loop = "true";
        this.ringbacktone.src = "/voip/static/src/sounds/ringbacktone.mp3";
        $("html").append(this.ringbacktone);
        this.incomingtone = document.createElement("audio");
        this.incomingtone.loop = "true";
        this.incomingtone.src = "/voip/static/src/sounds/incomingcall.mp3";
        $("html").append(this.incomingtone);
    },
    /**
     * Configure the audio media stream, at the begining of a call.
     *
     * @private
     */
    _configureRemoteAudio: function () {
        var call = this.sipSession;
        var peerConnection = call.sessionDescriptionHandler.peerConnection;
        var remoteStream = undefined;
        if (peerConnection.getReceivers) {
            remoteStream = new window.MediaStream();
            peerConnection.getReceivers().forEach(function (receiver) {
                var track = receiver.track;
                if (track) {
                    remoteStream.addTrack(track);
                }
            });
        } else {
            remoteStream = peerConnection.getRemoteStream()[0];
        }
        this.$remoteAudio.srcObject = remoteStream;
        this.$remoteAudio.play();
    },
    /**
     * Returns the ua after initialising it.
     *
     * @private
     * @param {Object} params user and pbx configuration parameters
     * @return {Object} the initialised ua
     */
    _createUa: function (params) {
        if (!(params.pbx_ip && params.wsServer)) {
            //TODO master: PBX or Websocket address is missing. Please check your settings.
            this._triggerError(_t('One or more parameter is missing. Please check your configuration.'))
            return false;
        }
        if (!(params.login && params.password)) {
            //TODO master: Your credentials are not correctly set. Please check your configuration.
            this._triggerError(_t('One or more parameter is missing. Please check your configuration.'));
            return false;
        }
        if (params.debug) {
            params.traceSip = true;
            params.log = {
                level: 3,
                builtinEnabled: true
            }
        } else {
            params.traceSip = false;
            params.log = {
                level: 2,
                builtinEnabled: false
            }
        }
        var uaConfig = this._getUaConfig(params);
        try {
            return new SIP.UA(uaConfig);
        } catch (err) {
            this._triggerError(_t('The server configuration could be wrong. Please check your configuration.'));
            return false;
        }
    },
    /**
    * Returns the ua configuration required.
    *
    * @private
    * @param {Object} params user and pbx configuration parameters
    * @return {Object} the ua configuration parameters
    */
    _getUaConfig: function (params) {
        var sessionDescriptionHandlerFactoryOptions = {
            constraints: {
                audio: true,
                video: false
            },
            iceCheckingTimeout: 1000,
        };
        return {
            uri: params.login + '@' + params.pbx_ip,
            transportOptions: {
                wsServers: params.wsServer || null,
                traceSip: params.traceSip
            },
            authorizationUser: params.login,
            password: params.password,
            hackIpInContact: true,
            registerExpires: 3600,
            register: true,
            sessionDescriptionHandlerFactoryOptions: sessionDescriptionHandlerFactoryOptions,
            log: params.log,
        };
    },
    /**
     * Initialises the ua, binds events and appends audio in the dom.
     *
     * @private
     * @param {Object} result user and pbx configuration return by the rpc
     */
    _initUa: function (result) {
        this.infoPbxConfiguration = result;
        this.mode = result.mode;
        if (this.mode === "prod") {
            this.trigger_up('sip_error', {msg: _t("Connecting..."), connecting: true});
            if (!window.RTCPeerConnection) {
                //TODO: In master, change the error message (Your browser does not support WebRTC. You will not be able to make or receive calls.)
                this._triggerError(_t('Your browser could not support WebRTC. Please check your configuration.'));
                return;
            }
            this.userAgent = this._createUa(result);
            if (!this.userAgent) {
                return;
            }
            this.alwaysTransfer = result.always_transfer;
            this.ignoreIncoming = result.ignore_incoming;
            if (result.external_phone) {
                this.externalPhone = clean_number(result.external_phone);
            }
            var self = this;
            // catch the error if the ws uri is wrong
            this.userAgent.transport.ws.onerror = function () {
                self._triggerError(_t('The websocket uri could be wrong.') +
                    _t(' Please check your configuration.'));
            };
            this.userAgent.on('registered', _.bind(this._onRegistered,this));
            this.userAgent.on('invite', _.bind(this._onInvite,this));
        }
        this._configureDomElements()
    },
    /**
     * Triggers the sip invite.
     *
     *  @param {String} number
     *  @private
     */
    _makeCall: function (number) {
        if (this.callState !== CALL_STATE.NO_CALL) {
            return;
        }
        try {
            number = clean_number(number);
            if (this.alwaysTransfer && this.externalPhone){
                this.sipSession = this.userAgent.invite(this.externalPhone);
                this.currentNumber = number;
            } else {
                this.sipSession = this.userAgent.invite(number);
            }
        } catch (err) {
            this._triggerError(_t('the connection cannot be made. ') +
                _t('Please check your configuration.</br> (Reason receives :') +
                err.reason_phrase + ')');
            return;
        }
        this._setupOutCall();
    },
    // TODO when the _sendNotification is moved into utils instead of mail.utils
    // remove this function and use the one in utils
    _sendNotification: function (title, content) {
        if (window.Notification && Notification.permission === "granted") {
            return new Notification(title,
                {body: content, icon: "/mail/static/src/img/odoo_o.png", silent: true});
        }
    },
    /**
     * Bind events to outgoing call.
     *
     * @private
     */
    _setupOutCall: function () {
        this.callState = CALL_STATE.RINGING_CALL;
        this.sipSession.on('accepted',_.bind(this._onAccepted,this));
        this.sipSession.on('cancel',_.bind(this._onCancel,this));
        this.sipSession.on('rejected',_.bind(this._onRejected,this));
    },
    /**
     * Toggle the sound of audio media stream
     *
     * @private
     * @param {boolean} mute
     */
    _toggleMute: function (mute) {
        var call = this.sipSession;
        var peerConnection = call.sessionDescriptionHandler.peerConnection;
        if (peerConnection.getSenders) {
            peerConnection.getSenders().forEach(function (sender) {
                if (sender.track) {
                    sender.track.enabled = !mute;
                }
            });
        } else {
            peerConnection.getLocalStreams().forEach(function (stream) {
                stream.getAudioTracks().forEach(function (track) {
                    track.enabled = !mute;
                });
            });
        }
    },
    /**
     * Triggers up an error.
     *
     * @private
     * @param {string} msg message diplayed
     * @param {boolean} temporary if the message can be discarded or not
     */
    _triggerError: function (msg, temporary) {
        this.trigger_up('sip_error', {msg:msg, temporary:temporary});
        this.blocked = true;
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Triggered when the call is answered.
     *
     * @private
     */
    _onAccepted: function () {
        this.callState = CALL_STATE.ONGOING_CALL;
        var call = this.sipSession;
        this.ringbacktone.pause();
        if (this.mode === 'prod') {
            this._configureRemoteAudio();
            call.sessionDescriptionHandler.on('addTrack',_.bind(this._configureRemoteAudio,this));
            call.on('bye',_.bind(this._onBye,this));
            if (this.alwaysTransfer && this.currentNumber){
                call.refer(this.currentNumber);
            }
        }
        this.trigger_up('sip_accepted');
    },
    /**
     * Handles the sip session ending.
     *
     * @private
     */
    _onBye: function () {
        this._cleanRemoteAudio();
        this.sipSession = false;
        this.callState = CALL_STATE.NO_CALL;
        this.trigger_up('sip_bye');
        if (this.mode === "demo") {
            clearTimeout(this.timerAccepted);
        }
    },
    /**
     * Handles the sip session cancel.
     *
     * @private
     */
    _onCancel: function () {
        this.sipSession = false;
        this.callState = CALL_STATE.NO_CALL;
        this.ringbacktone.pause();
        this.trigger_up('sip_cancel');
        if (this.mode === "demo") {
            clearTimeout(this.timerAccepted);
        }
    },
    /**
     * Handles the invite event.
     *
     * @param {Object} inviteSession
     */
    _onInvite: function (inviteSession) {
        if (this.ignoreIncoming || this.callState === CALL_STATE.ONGOING_CALL) {
            inviteSession.reject();
            return;
        }
        var self = this;
        var name = inviteSession.remoteIdentity.displayName;
        var number = inviteSession.remoteIdentity.uri.user;
        this._rpc({
            model: 'res.partner',
            method: 'search_read',
            domain: [
                '|',
                ['sanitized_phone', 'ilike', number],
                ['sanitized_mobile', 'ilike', number],
            ],
            fields: ['id', 'display_name'],
            limit: 1,
        }).then(function (contacts) {
            var incomingCallParams = {
                number: number
            };
            var contact = false;
            if (contacts.length) {
                contact = contacts[0];
                name = contact.display_name;
                incomingCallParams.partnerId = contact.id;
            }
            var content = _t("Incoming call from ");
            if (name) {
                content += name + ' (' + number + ')';
            } else {
                content += number;
            }
            self.incomingtone.currentTime = 0;
            self.incomingtone.play();

            self.notification = self._sendNotification('Odoo', content);
            function _rejectInvite () {
                if (!self.incomingCall) {
                    self.incomingtone.pause();
                    inviteSession.reject();
                }
            }
            inviteSession.on('rejected', function () {
                if (self.notification) {
                    self.notification.removeEventListener('close', _rejectInvite);
                    self.notification.close('rejected');
                    self.notification = undefined;
                    self.incomingtone.pause();
                } else if (self.dialog.$el.is(":visible")){
                    self.dialog.close();
                }
            });
            if (self.notification) {
                self.notification.onclick = function () {
                    window.focus();
                    self._answerCall(inviteSession, incomingCallParams);
                    this.close();
                };
                self.notification.addEventListener('close', _rejectInvite);
            } else {
                var options = {
                    confirm_callback: function () {
                        self._answerCall(inviteSession, incomingCallParams);
                    },
                    cancel_callback: function () {
                        try {
                            inviteSession.reject();
                        } catch (err) {
                            console.error('Reject failed:', err);
                        }
                        self.incomingtone.pause();
                    },
                };
                self.dialog = Dialog.confirm(self, content, options);
                self.dialog.on('closed', self, function () {
                    if (inviteSession && self.callState !== CALL_STATE.ONGOING_CALL) {
                        try {
                            inviteSession.reject();
                        } catch (err) {
                            console.error('Reject failed:', err);
                        }
                    }
                    self.incomingtone.pause();
                });
            }
        });
    },
    /**
     * Triggered when the user agent is connected.
     * This function will trigger the event 'sip_error_resolved' to unblock the
     * overlay
     *
     *  @private
     */
    _onRegistered: function (){
        this.trigger_up('sip_error_resolved');
    },
    /**
     * Handles the sip session rejection.
     *
     * @private
     * @param {Object} response
     */
    _onRejected: function (response) {
        if (this.sipSession) {
            this.sipSession = false;
            this.callState = CALL_STATE.NO_CALL;
            this.trigger_up('sip_rejected');
            this.ringbacktone.pause();
            if (response.status_code === 404 || response.status_code === 488) {
                this._triggerError(
                    _.str.sprintf(_t('The number is incorrect, the user credentials ' +
                                     'could be wrong or the connection cannot be made. ' +
                                     'Please check your configuration.</br> (Reason received: %s)'),
                        response.reason_phrase),
                    true);
            }
        }
    },
});

return UserAgent;

});
