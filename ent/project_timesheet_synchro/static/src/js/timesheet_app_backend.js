odoo.define('projcet_timesheet_synchro.app', function (require) {
'use strict';

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var IFrameWidget = require('web.IFrameWidget');

    var project_timesheet_synchro_demo = AbstractAction.extend({
        template: 'project_timesheet_synchro.demo',
        init: function(parent) {
            this._super(parent);
        },
        start: function(parent) {
            this._super(parent);
            if ($( window ).width() > 768) {
                new project_timesheet_synchro_app().appendTo(this.$el.find('.o_project_timesheet_app'));
            }
        },
    });

    var project_timesheet_synchro_app = IFrameWidget.extend({
        init: function(parent) {
            this._super(parent, '/project_timesheet_synchro/timesheet_app');
        },
        start: function(parent) {
        var res= this._super(parent);
        this.$el.css({height: '582px', width: '330px', border: 0});
        return res;
    },
    });

    core.action_registry.add('project_timesheet_synchro_app_action', project_timesheet_synchro_demo);

});