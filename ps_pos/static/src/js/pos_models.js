odoo.define('ps_point_of_sale.models', function (require) {
    "use strict";
    var models = require('point_of_sale.models');
    var BarcodeParser = require('barcodes.BarcodeParser');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var session = require('web.session');
    var utils = require('web.utils');

    var _t = core._t;
    var round_pr = utils.round_precision;

    models.PosModel = models.PosModel.extend({
        models: [
        {
            label:  'version',
            loaded: function(self){
                return session.rpc('/web/webclient/version_info',{}).done(function(version) {
                    self.version = version;
                });
            },

        },{
            model:  'res.users',
            fields: ['name','company_id'],
            ids:    function(self){ return [session.uid]; },
            loaded: function(self,users){ self.user = users[0]; },
        },{
            model:  'res.company',
            fields: [ 'currency_id', 'email', 'website', 'company_registry', 'vat', 'name', 'phone', 'partner_id' , 'country_id', 'tax_calculation_rounding_method'],
            ids:    function(self){ return [self.user.company_id[0]]; },
            loaded: function(self,companies){ self.company = companies[0]; },
        },{
            model:  'decimal.precision',
            fields: ['name','digits'],
            loaded: function(self,dps){
                self.dp  = {};
                for (var i = 0; i < dps.length; i++) {
                    self.dp[dps[i].name] = dps[i].digits;
                }
            },
        },{
            model:  'uom.uom',
            fields: [],
            domain: null,
            context: function(self){ return { active_test: false }; },
            loaded: function(self,units){
                self.units = units;
                _.each(units, function(unit){
                    self.units_by_id[unit.id] = unit;
                });
            }
        },{
            model:  'res.partner',
            fields: ['name','street','city','state_id','country_id','vat',
                     'phone','zip','mobile','email','barcode','write_date','ps_member_no','ps_member_category_id',
                     'property_account_position_id','property_product_pricelist','ps_member_state'],
            domain: [['customer','=',true]],
            loaded: function(self,partners){
                self.partners = partners;
                self.db.add_partners(partners);
            },
        },{
            model:  'ps.member.category',
            fields: ['name', 'ps_member_category_id'],
            loaded: function(self,ps_member_categories){
                self.ps_member_categories = ps_member_categories;
            },
        },{
            model:  'res.country',
            fields: ['name', 'vat_label'],
            loaded: function(self,countries){
                self.countries = countries;
                self.company.country = null;
                for (var i = 0; i < countries.length; i++) {
                    if (countries[i].id === self.company.country_id[0]){
                        self.company.country = countries[i];
                    }
                }
            },
        },{
            model:  'account.tax',
            fields: ['name','amount', 'price_include', 'include_base_amount', 'amount_type', 'children_tax_ids'],
            domain: function(self) {return [['company_id', '=', self.company && self.company.id || false]]},
            loaded: function(self, taxes){
                self.taxes = taxes;
                self.taxes_by_id = {};
                _.each(taxes, function(tax){
                    self.taxes_by_id[tax.id] = tax;
                });
                _.each(self.taxes_by_id, function(tax) {
                    tax.children_tax_ids = _.map(tax.children_tax_ids, function (child_tax_id) {
                        return self.taxes_by_id[child_tax_id];
                    });
                });
            },
        },{
            model:  'pos.session',
            fields: ['id', 'journal_ids','name','user_id','config_id','start_at','stop_at','sequence_number','login_number'],
            domain: function(self){ return [['state','=','opened'],['user_id','=',session.uid]]; },
            loaded: function(self,pos_sessions){
                self.pos_session = pos_sessions[0];
            },
        },{
            model: 'pos.config',
            fields: [],
            domain: function(self){ return [['id','=', self.pos_session.config_id[0]]]; },
            loaded: function(self,configs){
                self.config = configs[0];
                self.config.use_proxy = self.config.iface_payment_terminal ||
                                        self.config.iface_electronic_scale ||
                                        self.config.iface_print_via_proxy  ||
                                        self.config.iface_scan_via_proxy   ||
                                        self.config.iface_cashdrawer       ||
                                        self.config.iface_customer_facing_display;

                if (self.config.company_id[0] !== self.user.company_id[0]) {
                    throw new Error(_t("Error: The Point of Sale User must belong to the same company as the Point of Sale. You are probably trying to load the point of sale as an administrator in a multi-company setup, with the administrator account set to the wrong company."));
                }

                self.db.set_uuid(self.config.uuid);
                self.set_cashier(self.get_cashier());
                // We need to do it here, since only then the local storage has the correct uuid
                self.db.save('pos_session_id', self.pos_session.id);

                var orders = self.db.get_orders();
                for (var i = 0; i < orders.length; i++) {
                    self.pos_session.sequence_number = Math.max(self.pos_session.sequence_number, orders[i].data.sequence_number+1);
                }
           },
        },{
            model:  'res.users',
            fields: ['name','pos_security_pin','groups_id','barcode'],
            domain: function(self){ return [['company_id','=',self.user.company_id[0]],'|', ['groups_id','=', self.config.group_pos_manager_id[0]],['groups_id','=', self.config.group_pos_user_id[0]]]; },
            loaded: function(self,users){
                // we attribute a role to the user, 'cashier' or 'manager', depending
                // on the group the user belongs.
                var pos_users = [];
                var current_cashier = self.get_cashier();
                for (var i = 0; i < users.length; i++) {
                    var user = users[i];
                    for (var j = 0; j < user.groups_id.length; j++) {
                        var group_id = user.groups_id[j];
                        if (group_id === self.config.group_pos_manager_id[0]) {
                            user.role = 'manager';
                            break;
                        } else if (group_id === self.config.group_pos_user_id[0]) {
                            user.role = 'cashier';
                        }
                    }
                    if (user.role) {
                        pos_users.push(user);
                    }
                    // replace the current user with its updated version
                    if (user.id === self.user.id) {
                        self.user = user;
                    }
                    if (user.id === current_cashier.id) {
                        self.set_cashier(user);
                    }
                }
                self.users = pos_users;
            },
        },{
            model: 'stock.location',
            fields: [],
            ids:    function(self){ return [self.config.stock_location_id[0]]; },
            loaded: function(self, locations){ self.shop = locations[0]; },
        },{
            model:  'product.pricelist',
            fields: ['name', 'display_name'],
            domain: function(self) { return [['id', 'in', self.config.available_pricelist_ids]]; },
            loaded: function(self, pricelists){
                _.map(pricelists, function (pricelist) { pricelist.items = []; });
                self.default_pricelist = _.findWhere(pricelists, {id: self.config.pricelist_id[0]});
                self.pricelists = pricelists;
            },
        },{
            model:  'product.pricelist.item',
            domain: function(self) { return [['pricelist_id', 'in', _.pluck(self.pricelists, 'id')]]; },
            loaded: function(self, pricelist_items){
                var pricelist_by_id = {};
                _.each(self.pricelists, function (pricelist) {
                    pricelist_by_id[pricelist.id] = pricelist;
                });

                _.each(pricelist_items, function (item) {
                    var pricelist = pricelist_by_id[item.pricelist_id[0]];
                    pricelist.items.push(item);
                    item.base_pricelist = pricelist_by_id[item.base_pricelist_id[0]];
                });
            },
        },{
            model:  'product.category',
            fields: ['name', 'parent_id'],
            loaded: function(self, product_categories){
                var category_by_id = {};
                _.each(product_categories, function (category) {
                    category_by_id[category.id] = category;
                });
                _.each(product_categories, function (category) {
                    category.parent = category_by_id[category.parent_id[0]];
                });

                self.product_categories = product_categories;
            },
        },{
            model: 'res.currency',
            fields: ['name','symbol','position','rounding','rate'],
            ids:    function(self){ return [self.config.currency_id[0], self.company.currency_id[0]]; },
            loaded: function(self, currencies){
                self.currency = currencies[0];
                if (self.currency.rounding > 0 && self.currency.rounding < 1) {
                    self.currency.decimals = Math.ceil(Math.log(1.0 / self.currency.rounding) / Math.log(10));
                } else {
                    self.currency.decimals = 0;
                }

                self.company_currency = currencies[1];
            },
        },{
            model:  'pos.category',
            fields: ['id', 'name', 'parent_id', 'child_id'],
            domain: null,
            loaded: function(self, categories){
                self.db.add_categories(categories);
            },
        },{
            model:  'product.product',
            // todo remove list_price in master, it is unused
            fields: ['display_name', 'list_price', 'lst_price', 'standard_price', 'categ_id', 'pos_categ_id', 'taxes_id',
                     'barcode', 'default_code', 'to_weight', 'uom_id', 'description_sale', 'description',
                     'product_tmpl_id','tracking'],
            order:  _.map(['sequence','default_code','name'], function (name) { return {name: name}; }),
            domain: [['sale_ok','=',true],['available_in_pos','=',true]],
            context: function(self){ return { display_default_code: false }; },
            loaded: function(self, products){
                var using_company_currency = self.config.currency_id[0] === self.company.currency_id[0];
                var conversion_rate = self.currency.rate / self.company_currency.rate;
                self.db.add_products(_.map(products, function (product) {
                    if (!using_company_currency) {
                        product.lst_price = round_pr(product.lst_price * conversion_rate, self.currency.rounding);
                    }
                    product.categ = _.findWhere(self.product_categories, {'id': product.categ_id[0]});
                    return new models.Product({}, product);
                }));
            },
        },{
            model:  'account.bank.statement',
            fields: ['account_id','currency_id','journal_id','state','name','user_id','pos_session_id'],
            domain: function(self){ return [['state', '=', 'open'],['pos_session_id', '=', self.pos_session.id]]; },
            loaded: function(self, cashregisters, tmp){
                self.cashregisters = cashregisters;

                tmp.journals = [];
                _.each(cashregisters,function(statement){
                    tmp.journals.push(statement.journal_id[0]);
                });
            },
        },{
            model:  'account.journal',
            fields: ['type', 'sequence'],
            domain: function(self,tmp){ return [['id','in',tmp.journals]]; },
            loaded: function(self, journals){
                var i;
                self.journals = journals;

                // associate the bank statements with their journals.
                var cashregisters = self.cashregisters;
                var ilen = cashregisters.length;
                for(i = 0; i < ilen; i++){
                    for(var j = 0, jlen = journals.length; j < jlen; j++){
                        if(cashregisters[i].journal_id[0] === journals[j].id){
                            cashregisters[i].journal = journals[j];
                        }
                    }
                }

                self.cashregisters_by_id = {};
                for (i = 0; i < self.cashregisters.length; i++) {
                    self.cashregisters_by_id[self.cashregisters[i].id] = self.cashregisters[i];
                }

                self.cashregisters = self.cashregisters.sort(function(a,b){
                    // prefer cashregisters to be first in the list
                    if (a.journal.type == "cash" && b.journal.type != "cash") {
                        return -1;
                    } else if (a.journal.type != "cash" && b.journal.type == "cash") {
                        return 1;
                    } else {
                        return a.journal.sequence - b.journal.sequence;
                    }
                });

            },
        },  {
            model:  'account.fiscal.position',
            fields: [],
            domain: function(self){ return [['id','in',self.config.fiscal_position_ids]]; },
            loaded: function(self, fiscal_positions){
                self.fiscal_positions = fiscal_positions;
            }
        }, {
            model:  'account.fiscal.position.tax',
            fields: [],
            domain: function(self){
                var fiscal_position_tax_ids = [];

                self.fiscal_positions.forEach(function (fiscal_position) {
                    fiscal_position.tax_ids.forEach(function (tax_id) {
                        fiscal_position_tax_ids.push(tax_id);
                    });
                });

                return [['id','in',fiscal_position_tax_ids]];
            },
            loaded: function(self, fiscal_position_taxes){
                self.fiscal_position_taxes = fiscal_position_taxes;
                self.fiscal_positions.forEach(function (fiscal_position) {
                    fiscal_position.fiscal_position_taxes_by_id = {};
                    fiscal_position.tax_ids.forEach(function (tax_id) {
                        var fiscal_position_tax = _.find(fiscal_position_taxes, function (fiscal_position_tax) {
                            return fiscal_position_tax.id === tax_id;
                        });

                        fiscal_position.fiscal_position_taxes_by_id[fiscal_position_tax.id] = fiscal_position_tax;
                    });
                });
            }
        },  {
            label: 'fonts',
            loaded: function(){
                var fonts_loaded = new $.Deferred();
                // Waiting for fonts to be loaded to prevent receipt printing
                // from printing empty receipt while loading Inconsolata
                // ( The font used for the receipt )
                waitForWebfonts(['Lato','Inconsolata'], function(){
                    fonts_loaded.resolve();
                });
                // The JS used to detect font loading is not 100% robust, so
                // do not wait more than 5sec
                setTimeout(function(){
                    fonts_loaded.resolve();
                },5000);

                return fonts_loaded;
            },
        },{
            label: 'pictures',
            loaded: function(self){
                self.company_logo = new Image();
                var  logo_loaded = new $.Deferred();
                self.company_logo.onload = function(){
                    var img = self.company_logo;
                    var ratio = 1;
                    var targetwidth = 300;
                    var maxheight = 150;
                    if( img.width !== targetwidth ){
                        ratio = targetwidth / img.width;
                    }
                    if( img.height * ratio > maxheight ){
                        ratio = maxheight / img.height;
                    }
                    var width  = Math.floor(img.width * ratio);
                    var height = Math.floor(img.height * ratio);
                    var c = document.createElement('canvas');
                        c.width  = width;
                        c.height = height;
                    var ctx = c.getContext('2d');
                        ctx.drawImage(self.company_logo,0,0, width, height);

                    self.company_logo_base64 = c.toDataURL();
                    logo_loaded.resolve();
                };
                self.company_logo.onerror = function(){
                    logo_loaded.reject();
                };
                self.company_logo.crossOrigin = "anonymous";
                self.company_logo.src = '/web/binary/company_logo' +'?dbname=' + session.db + '&_'+Math.random();

                return logo_loaded;
            },
        }, {
            label: 'barcodes',
            loaded: function(self) {
                var barcode_parser = new BarcodeParser({'nomenclature_id': self.config.barcode_nomenclature_id});
                self.barcode_reader.set_barcode_parser(barcode_parser);
                return barcode_parser.is_loaded();
            },
        }
        ],
    });

    models.Order = models.Order.extend({
        get_total_offer: function() {
            return round_pr(this.orderlines.reduce((function(sum, orderLine) {
                return sum + ((orderLine.product.list_price - orderLine.get_unit_display_price()) * orderLine.get_quantity());
            }), 0), this.pos.currency.rounding);
        },
        export_for_printing: function(){
            var orderlines = [];
            var self = this;

            this.orderlines.each(function(orderline){
                orderlines.push(orderline.export_for_printing());
            });

            var paymentlines = [];
            this.paymentlines.each(function(paymentline){
                paymentlines.push(paymentline.export_for_printing());
            });
            var client  = this.get('client');
            var cashier = this.pos.get_cashier();
            var company = this.pos.company;
            var shop    = this.pos.shop;
            var date    = new Date();

            function is_xml(subreceipt){
                return subreceipt ? (subreceipt.split('\n')[0].indexOf('<!DOCTYPE QWEB') >= 0) : false;
            }

            function render_xml(subreceipt){
                if (!is_xml(subreceipt)) {
                    return subreceipt;
                } else {
                    subreceipt = subreceipt.split('\n').slice(1).join('\n');
                    var qweb = new QWeb2.Engine();
                        qweb.debug = core.debug;
                        qweb.default_dict = _.clone(QWeb.default_dict);
                        qweb.add_template('<templates><t t-name="subreceipt">'+subreceipt+'</t></templates>');

                    return qweb.render('subreceipt',{'pos':self.pos,'widget':self.pos.chrome,'order':self, 'receipt': receipt}) ;
                }
            }

            var receipt = {
                orderlines: orderlines,
                paymentlines: paymentlines,
                subtotal: this.get_subtotal(),
                total_with_tax: this.get_total_with_tax(),
                total_without_tax: this.get_total_without_tax(),
                total_tax: this.get_total_tax(),
                total_paid: this.get_total_paid(),
                total_discount: this.get_total_discount(),
                total_offer: this.get_total_offer(),
                tax_details: this.get_tax_details(),
                change: this.get_change(),
                name : this.get_name(),
                client: client ? client.name : null ,
                invoice_id: null,   //TODO
                cashier: cashier ? cashier.name : null,
                precision: {
                    price: 2,
                    money: 2,
                    quantity: 3,
                },
                date: {
                    year: date.getFullYear(),
                    month: date.getMonth(),
                    date: date.getDate(),       // day of the month
                    day: date.getDay(),         // day of the week
                    hour: date.getHours(),
                    minute: date.getMinutes() ,
                    isostring: date.toISOString(),
                    localestring: date.toLocaleString(),
                },
                company:{
                    email: company.email,
                    website: company.website,
                    company_registry: company.company_registry,
                    contact_address: company.partner_id[1],
                    vat: company.vat,
                    vat_label: company.country && company.country.vat_label || '',
                    name: company.name,
                    phone: company.phone,
                    logo:  this.pos.company_logo_base64,
                },
                shop:{
                    name: shop.name,
                },
                currency: this.pos.currency,
            };

            if (is_xml(this.pos.config.receipt_header)){
                receipt.header = '';
                receipt.header_xml = render_xml(this.pos.config.receipt_header);
            } else {
                receipt.header = this.pos.config.receipt_header || '';
            }

            if (is_xml(this.pos.config.receipt_footer)){
                receipt.footer = '';
                receipt.footer_xml = render_xml(this.pos.config.receipt_footer);
            } else {
                receipt.footer = this.pos.config.receipt_footer || '';
            }

            return receipt;
        },
    })

});
