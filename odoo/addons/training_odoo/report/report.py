import time
from openerp.report import report_sxw

class print_training(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(print_training, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
        })


report_sxw.report_sxw('report.laporan.kursus', 'training.kursus',
                      'addons/training_odoo/report/print_kursus.rml', parser=print_training, header=False)
