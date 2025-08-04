from odoo import api, fields, models, _
from odoo.fields import Date

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
        'account.payment.method.line',
        compute='_compute_payment_method_line_id',
        readonly=False, store=True, copy=False,
        
        domain="[('id', 'in', available_payment_method_line_ids)]",
        string='Payment Method'

    )
    available_payment_method_line_ids = fields.Many2many('account.payment.method.line',
        compute='_compute_payment_method_line_fields')
    
    payment_journal_id = fields.Many2one(
        'account.journal',
        domain="[('id', 'in', available_payment_journal_ids)]",
        string ='Payment Journal'
    )
    available_payment_journal_ids = fields.Many2many(
        comodel_name='account.journal',
        compute='_compute_available_payment_journal_ids'
    )
    @api.depends('available_payment_method_line_ids')
    def _compute_payment_method_line_id(self):
        ''' Compute the 'payment_method_line_id' field.
        This field is not computed in '_compute_payment_method_line_fields' because it's a stored editable one.
        '''
        print("dkflsdkf")
        for pay in self:
            available_payment_method_lines = pay.available_payment_method_line_ids

            # Select the first available one by default.
            if pay.payment_method_id in available_payment_method_lines:
                pay.payment_method_id = pay.payment_method_id
            elif available_payment_method_lines:
                pay.payment_method_id = available_payment_method_lines[0]._origin
            else:
                pay.payment_method_id = False
    @api.depends( 'payment_journal_id')
    def _compute_payment_method_line_fields(self):
        for pay in self:
            pay.available_payment_method_line_ids = pay.payment_journal_id._get_available_payment_method_lines('inbound')
            to_exclude = pay._get_payment_method_codes_to_exclude()
            if to_exclude:
                pay.available_payment_method_line_ids = pay.available_payment_method_line_ids.filtered(lambda x: x.code not in to_exclude)
    @api.depends('company_id')
    def _compute_available_payment_journal_ids(self):
        """
        Get all journals having at least one payment method for inbound/outbound depending on the payment_type.
        """
        journals = self.env['account.journal'].search([
            '|',
            ('company_id', 'parent_of', self.env.company.id),
            ('company_id', 'child_of', self.env.company.id),
            ('type', 'in', ('bank', 'cash')),
        ])
        print("payment_journal_id")
        for pay in self:
            # if pay.payment_type == 'inbound':
            print("payment_journal_id")
            pay.available_payment_journal_ids = journals.filtered('inbound_payment_method_line_ids')
            # else:
                # pay.available_journal_ids = journals.filtered('outbound_payment_method_line_ids')

    def _get_payment_method_codes_to_exclude(self):
        # can be overriden to exclude payment methods based on the payment characteristics
        self.ensure_one()
        return []

    @api.model
    def create(self, vals):
        move = super().create(vals)
        # for rec in vals:
        # if vals.get('mo_payment_type') == 'ghair_ajil' :

        #     move._create_instant_payment()
        return move
    
    def action_post(self):
        self._create_instant_payment()
        print("actino post ###########################################################")
        super().action_post()
        
        return False
    
    def _create_instant_payment(self):
        self.ensure_one()
        payment_vals = {
            'payment_type': 'inbound',
            'payment_method_id':self.payment_method_id.id,
            'partner_id': self.partner_id.id,
            'amount': self.amount_total,
            'date': Date.today(),
            'ref': self.name,
            'payment_method_line_id': self.payment_method_id.id,
            'journal_id': self.payment_journal_id.id,
            
            'reconciled_invoice_ids': [(6, 0, [self.id])]
            
        }
        print(payment_vals)
        payment = self.env['account.payment'].create(payment_vals)
        # payment.action_post()