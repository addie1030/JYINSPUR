# -*- coding: utf-8 -*-

import collections
from functools import partial

import babel.dates
from dateutil.relativedelta import relativedelta, MO, SU

from odoo import _, api, models
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.misc import format_date

_GRID_TUP = [('grid', "Grid")]


class Base(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def read_grid(self, row_fields, col_field, cell_field, domain=None, range=None):
        """
        Current anchor (if sensible for the col_field) can be provided by the
        ``grid_anchor`` value in the context

        :param list[str] row_fields: group row header fields
        :param str col_field: column field
        :param str cell_field: cell field, summed
        :param range: displayed range for the current page
        :type range: None | {'step': object, 'span': object}
        :type domain: None | list
        :returns: dict of prev context, next context, matrix data, row values
                  and column values
        """
        domain = expression.normalize_domain(domain)
        column_info = self._grid_column_info(col_field, range)

        # [{ __count, __domain, grouping, **row_fields, cell_field }]
        groups = self._read_group_raw(
            expression.AND([domain, column_info.domain]),
            [col_field, cell_field] + row_fields,
            [column_info.grouping] + row_fields,
            lazy=False
        )

        row_key = lambda it, fs=row_fields: tuple(it[f] for f in fs)

        # [{ values: { field1: value1, field2: value2 } }]
        rows = self._grid_get_row_headers(row_fields, groups, key=row_key)
        # column_info.values is a [(value, label)] seq
        # convert to [{ values: { col_field: (value, label) } }]
        cols = column_info.values

        # map of cells indexed by row_key (tuple of row values) then column value
        cell_map = collections.defaultdict(dict)
        for group in groups:
            row = row_key(group)
            col = column_info.format(group[column_info.grouping])
            cell_map[row][col] = self._grid_format_cell(group, cell_field)

        # pre-build whole grid, row-major, h = len(rows), w = len(cols),
        # each cell is
        #
        # * size (number of records)
        # * value (accumulated cell_field)
        # * domain (domain for the records of that cell
        grid = []
        for r in rows:
            row = []
            grid.append(row)
            r_k = row_key(r['values'])
            for c in cols:
                col_value = c['values'][col_field][0]
                it = cell_map[r_k].get(col_value)
                if it: # accumulated cell exists, just use it
                    row.append(it)
                else:
                    # generate de novo domain for the cell
                    # The domain of the cell is the combination of the domain of the row, the
                    # column and the view.
                    d = expression.AND([r['domain'], c['domain'], domain])
                    row.append(self._grid_make_empty_cell(d))
                row[-1]['is_current'] = c.get('is_current', False)

        return {
            'prev': column_info.prev,
            'next': column_info.next,
            'initial': column_info.initial,
            'cols': cols,
            'rows': rows,
            'grid': grid,
        }

    def _grid_make_empty_cell(self, cell_domain):
        return {'size': 0, 'domain': cell_domain, 'value': 0}

    def _grid_format_cell(self, group, cell_field):
        return {
            'size': group['__count'],
            'domain': group['__domain'],
            'value': group[cell_field],
        }

    def _grid_get_row_headers(self, row_fields, groups, key):
        seen = {}
        rows = []
        for cell in groups:
            k = key(cell)
            if k in seen:
                seen[k][1].append(cell['__domain'])
            else:
                r = (
                    {f: cell[f] for f in row_fields},
                    [cell['__domain']],
                )
                seen[k] = r
                rows.append(r)

        # TODO: generates pretty long domains, is there a way to simplify them?
        return [
            {'values': values, 'domain': expression.OR(domains)}
            for values, domains in rows
        ]

    def _grid_column_info(self, name, range):
        """
        :param str name:
        :param range:
        :type range: None | dict
        :rtype: ColumnMetadata
        """
        if not range:
            range = {}
        field = self._fields[name]
        context_anchor = self.env.context.get('grid_anchor')

        if field.type == 'selection':
            return ColumnMetadata(
                grouping=name,
                domain=[],
                prev=False,
                next=False,
                initial=False,
                values=[{
                        'values': { name: v },
                        'domain': [(name, '=', v[0])],
                        'is_current': False
                    } for v in field._description_selection(self.env)
                ],
                format=lambda a: a,
            )
        elif field.type == 'many2one':
            return ColumnMetadata(
                grouping=name,
                domain=[],
                prev=False,
                next=False,
                initial=False,
                values=[{
                        'values': { name: v },
                        'domain': [(name, '=', v[0])],
                        'is_current': False
                    } for v in self.env[field.comodel_name].search([]).name_get()
                ],
                format=lambda a: a and a[0],
            )
        elif field.type == 'date':
            # seemingly sane defaults
            step = range.get('step', 'day')
            span = range.get('span', 'month')

            today = anchor = field.from_string(field.context_today(self))
            if context_anchor:
                anchor = field.from_string(context_anchor)

            r = self._grid_range_of(span, step, anchor)
            pagination = self._grid_pagination(field, span, step, anchor)
            return ColumnMetadata(
                grouping='{}:{}'.format(name, step),
                domain=[
                    '&',
                    (name, '>=', field.to_string(r.start)),
                    (name, '<=', field.to_string(r.end))
                ],
                prev=pagination.get('prev'),
                next=pagination.get('next'),
                initial=pagination.get('initial'),
                values=[{
                        'values': {
                            name: self._get_date_column_label(d, field, span, step)
                        },
                        'domain': ['&',
                                   (name, '>=', field.to_string(d)),
                                   (name, '<', field.to_string(d + self._grid_step_by(step)))],
                        'is_current': self._grid_date_is_current(field, span, step, d)
                    } for d in r.iter(step)
                ],
                format=lambda a: a and a[0],
            )
        else:
            raise ValueError(_("Can not use fields of type %s as grid columns") % field.type)

    @api.model
    def read_grid_domain(self, field, range):
        """ JS grid view may need to know the "span domain" of the grid before
        it has been able to read the grid at all. This provides only that part
        of the grid processing

        .. warning:: the result domain *must* be properly normalized
        """
        if not range:
            range = {}
        field = self._fields[field]
        if field.type == 'selection':
            return []
        elif field.type == 'many2one':
            return []
        elif field.type == 'date':
            step = range.get('step', 'day')
            span = range.get('span', 'month')

            anchor = field.from_string(field.context_today(self))
            context_anchor = self.env.context.get('grid_anchor')
            if context_anchor:
                anchor = field.from_string(context_anchor)

            r = self._grid_range_of(span, step, anchor)
            return [
                '&',
                (field.name, '>=', field.to_string(r.start)),
                (field.name, '<=', field.to_string(r.end))
            ]
        raise UserError(_("Can not use fields of type %s as grid columns") % field.type)

    def _get_date_column_label(self, date, field, span, step):
        """
            :param date: date of period beginning (datetime object)
            :param field: odoo.field object of the current model
        """
        locale = self.env.context.get('lang', 'en_US')
        _labelize = self._get_date_formatter(step, locale=locale)
        label = _labelize(date)
        if step == 'week':
            label = _("Week %(weeknumber)s\n%(week_start)s - %(week_end)s") % {
                'weeknumber': label,
                'week_start': format_date(self.env, date, locale, "MMM\u00A0dd"),
                'week_end': format_date(self.env, date + self._grid_step_by(step) - relativedelta(days=1), locale, "MMM\u00A0dd")
            }
        return ("%s/%s" % (field.to_string(date), field.to_string(date + self._grid_step_by(step))), label)

    def _get_date_formatter(self, step, locale):
        """ Returns a callable taking a single positional date argument and
        formatting it for the step and locale provided.
        """
        if hasattr(babel.dates, 'format_skeleton') and step != 'week':
            def _format(d, _fmt=babel.dates.format_skeleton, _sk=SKELETONS[step], _l=locale):
                result = _fmt(datetime=d, skeleton=_sk, locale=_l)
                # approximate distribution over two lines, for better
                # precision should be done by rendering with an actual
                # proportional font, for even better precision should be done
                # using the fonts the browser asks for, here we just use
                # non-whitespace length which is really gross. Also may need
                # word-splitting in non-latin scripts.
                #
                # also ideally should not split the lines at all under a
                # certain width
                cl = lambda l: sum(len(s) for s in l)
                line1 = result.split(u' ')
                halfway = cl(line1) / 2.
                line2 = collections.deque(maxlen=int(halfway) + 1)
                while cl(line1) > halfway:
                    line2.appendleft(line1.pop())

                middle = line2.popleft()
                if cl(line1) < cl(line2):
                    line1.append(middle)
                else:
                    line2.appendleft(middle)

                return u"%s\n%s" % (
                    u'\u00A0'.join(line1),
                    u'\u00A0'.join(line2),
                )
            return _format
        else:
            return partial(babel.dates.format_date,
                           format=FORMAT[step],
                           locale=locale)

    def _grid_pagination(self, field, span, step, anchor):
        if field.type == 'date':
            today = field.from_string(field.context_today(self))
            diff = self._grid_step_by(span)
            period_prev = field.to_string(anchor - diff)
            period_next = field.to_string(anchor + diff)
            return {
                'prev': {'grid_anchor': period_prev, 'default_%s' % field.name: period_prev},
                'next': {'grid_anchor': period_next, 'default_%s' % field.name: period_next},
                'initial': {'grid_anchor': field.to_string(today), 'default_%s' % field.name: field.to_string(today)}
            }
        return dict.fromkeys(['prev', 'initial', 'next'], False)

    def _grid_step_by(self, span):
        return STEP_BY.get(span)

    def _grid_range_of(self, span, step, anchor):
        return date_range(self._grid_start_of(span, step, anchor),
                          self._grid_end_of(span, step, anchor))

    def _grid_start_of(self, span, step, anchor):
        if step == 'week':
            return anchor + START_OF_WEEK[span]
        return anchor + START_OF[span]

    def _grid_end_of(self, span, step, anchor):
        if step == 'week':
            return anchor + END_OF_WEEK[span]
        return anchor + END_OF[span]

    def _grid_start_of_period(self, span, step, anchor):
        if step == 'day':
            return anchor
        return anchor + START_OF[step]

    def _grid_end_of_period(self, span, step, anchor):
        if step == 'day':
            return anchor
        return anchor + END_OF[step]

    def _grid_date_is_current(self, field, span, step, date):
        today = field.from_string(field.context_today(self))
        if step == 'day':
            return today == date
        elif step in ['week', 'month']:
            return self._grid_start_of_period(span, step, date) <= today < self._grid_end_of_period(span, step, date)
        return False


ColumnMetadata = collections.namedtuple('ColumnMetadata', 'grouping domain prev next initial values format')
class date_range(object):
    def __init__(self, start, stop):
        assert start < stop
        self.start = start
        self.end = stop

    def iter(self, step):
        v = self.start
        step = STEP_BY[step]
        while v <= self.end:
            yield v
            v += step

START_OF = {
    'week': relativedelta(weekday=MO(-1)),
    'month': relativedelta(day=1),
    'year': relativedelta(yearday=1),
}
START_OF_WEEK = {
    'week': relativedelta(weekday=MO(-1)),
    'month': relativedelta(day=1, weekday=MO(-1)),
    'year': relativedelta(yearday=1, weekday=MO(-1)),
}
END_OF = {
    'week': relativedelta(weekday=SU),
    'month': relativedelta(months=1, day=1, days=-1),
    'year': relativedelta(years=1, yearday=1, days=-1),
}
END_OF_WEEK = {
    'week': relativedelta(weekday=SU),
    'month': relativedelta(months=1, day=1, days=-1, weekday=SU),
    'year': relativedelta(years=1, yearday=1, days=-1, weekday=SU),
}
STEP_BY = {
    'day': relativedelta(days=1),
    'week': relativedelta(weeks=1),
    'month': relativedelta(months=1),
    'year': relativedelta(years=1),
}

FORMAT = {
    'day': u"EEE\nMMM\u00A0dd",
    'week': u'w',
    'month': u'MMMM\u00A0yyyy',
}
SKELETONS = {
    'day': u"MMMEEEdd",
    'month': u'yyyyMMMM',
}
