from odoo import api, fields, models, _

class AccountMove(models.Model):
    _inherit = 'account.move'

    mo_payment_type = fields.Selection(
        selection=[
            ('ajil', 'أجل'),
            ('ghair_ajil', 'غير أجل'),
        ],
        string='Payment Type'
    )

    payment_method_id = fields.Many2one(
        'account.payment.method',
        string='Payment Method'
    )
    @api.model
    def create(self, vals):
        move = super().create(vals)
        if vals.get('payment_type') == 'ghair_ajil' and move.move_type == 'out_invoice':
            
            move._create_instant_payment()
        return move

    def _create_instant_payment(self):
        payment_vals = {
            'payment_type': 'inbound',
            'partner_id': self.partner_id.id,
            'amount': self.amount_total,
            'payment_method_id': self.payment_method_id.id,
            'journal_id': self.journal_id.id,
            'payment_date': fields.Date.today(),
            'effective_date': fields.Date.today(),
            'communication': self.name,
            'invoice_ids': [(6, 0, [self.id])]
        }
        print(payment_vals)
        payment = self.env['account.payment'].create(payment_vals)
        payment.action_post()