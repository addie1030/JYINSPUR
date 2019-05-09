odoo.define('marketing_automation.activity_graph', function (require) {
'use strict';

var AbstractField = require('web.AbstractField');
var registry = require('web.field_registry');

var ActivityGraph = AbstractField.extend({
    className: 'o_ma_activity_graph',
    cssLibs: [
        '/web/static/lib/nvd3/nv.d3.css',
    ],
    jsLibs: [
        '/web/static/lib/nvd3/d3.v3.js',
        '/web/static/lib/nvd3/nv.d3.js',
        '/web/static/src/js/libs/nvd3.js',
    ],

    /**
     * @private
     * @override _init to set data
     */
    init: function () {
        this._super.apply(this, arguments);
        this.data = JSON.parse(this.value);
    },

    /**
     * @private
     * @override _render
     */
    _render: function () {
        var self = this;
        if(!self.data || !_.isArray(self.data)){
            return;
        }
        this.chart = null;
        this.$el.empty().append('<svg>');
        nv.addGraph(function () {
            var indexMap = _.map(self.data[0].values, function (v) {
                return v.x;
            });
            self.chart = nv.models.lineChart().useInteractiveGuideline(true);
            self.chart.forceY([0]);
            self.chart.options({
                x: function (d) { return indexMap.indexOf(d.x); },
                margin: {'left': 25, 'right': 20, 'top': 5, 'bottom': 20},
                showYAxis: false,
                showLegend: false
            });
            self.chart.xAxis.tickFormat(function (tick) {
                var label = '';
                _.each(self.data, function (d) {
                    if (d.values[tick] && d.values[tick].x) {
                        label = d.values[tick].x;
                    }
                });
                return label;
            });

            d3.select(self.$('svg')[0])
                .datum(self.data)
                .transition().duration(1200)
                .call(self.chart);

            $(window).trigger('resize');
        });
    },
});

registry.add('marketing_activity_graph', ActivityGraph);

return ActivityGraph;

});
