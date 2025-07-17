from odoo import models, fields, api

class GithubSyncWizard(models.TransientModel):
    _name = 'github.sync.wizard'
    _description = 'GitHub Synchronization Wizard'

    def sync_all_repositories(self):
        self.env['github.repository'].search([]).sync_repository_data()
        return {'type': 'ir.actions.act_window_close'}