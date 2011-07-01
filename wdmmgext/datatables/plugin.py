try:
    import json 
except ImportError:
    import simplejson as json

from pprint import pprint
from pylons.i18n import get_lang, _
from genshi.filters import Transformer
from genshi.input import HTML

from wdmmg.model import Dimension
from wdmmg.lib import helpers as h
from wdmmg.plugins import SingletonPlugin, implements
from wdmmg.plugins import IGenshiStreamFilter 

HEAD_SNIPPET = """
<link rel="stylesheet" type="text/css" href="/css/data_tables.css" />
<script src="/js/jquery.dataTables.min.js"></script>
<script src="/js/datatables.js"></script>
"""

TABLE_SNIPPET = """
<table cellpadding="0" cellspacing="0" border="0" class="data_table" id="data_table">
    <thead>
        <tr>
            <th>%(name)s</th>
            <th class="">%(amount)s</th>
            <th class="">%(percentage)s</th>
            <th class="">%(change)s</th>
        </tr>
    </thead>
    <tbody>
        %(rows)s
    </tbody>
</table>
"""

ROW_SNIPPET = """ 
        <tr>
            <td>%(name)s</td>
            <td class="num">%(amount)s</td>
            <td class="num">%(percentage)s</td>
            <td class="num">%(change)s</td>
        </tr>
"""

class DataTablesGenshiStreamFilter(SingletonPlugin):
    implements(IGenshiStreamFilter, inherit=True)

    def filter(self, stream):
        from pylons import tmpl_context as c 
        if hasattr(c, 'viewstate') and hasattr(c, 'time'):
            if len(c.viewstate.aggregates): 
                breakdown = c.viewstate.view.drilldown
                km = Dimension.find_one({'key': breakdown, 
                                         'dataset': c.dataset.name})
                if km: 
                    breakdown = km.get('label') or breakdown
                columns = {
                    'name': _("Name"), 
                    'amount': _("Amount (%s)") % c.viewstate.view.dataset.get('currency'),
                    'percentage': _("Percentage"),
                    'change': _("Change +/-"),
                    'breakdown': breakdown 
                }
                rows = self._transform_rows(c.viewstate.aggregates, 
                        c.time, c.time_before, c.viewstate.totals)
                columns['rows'] = "\n".join([ROW_SNIPPET % row for row in rows])
                stream = stream | Transformer('html/head')\
                    .append(HTML(HEAD_SNIPPET))
                stream = stream | Transformer('//div[@id="detail"]')\
                    .after(HTML(TABLE_SNIPPET % columns))
        return stream

    def _transform_rows(self, aggregates, time, time_before, totals):
        rows = []
        total = totals.get(time)
        #total_before = totals.get(time_before)
        for obj, values in aggregates: 
            row = {}
            row['name'] = h.dimension_link(obj)
            value = values.get(time)
            if value is not None:
                row['amount'] = h.format_number_with_commas(value)
            else: 
                row['amount'] = '-'
            if total is not None and value is not None:
                share = abs(float(value))/max(1.0,abs(float(total))) * 100.0
                row['percentage'] = "%.2f%%" % share
            else:
                row['percentage'] = '-'
            before = values.get(time_before, 0.0)
            if (value is not None) and before > 0:
                change = ((value - before)/before) * 100
                if value >= before:
                    row['change'] = "<span class='growth'>+%.2f%%</span>" % change
                else:
                    row['change'] = "<span class='shrink'>%.2f%%</span>" % change
            else:
                row['change'] = '-'
            rows.append(row)
        return rows


