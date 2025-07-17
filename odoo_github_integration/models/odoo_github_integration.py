from odoo import models, fields, api
import requests
import base64
import json
import logging

_logger = logging.getLogger(__name__)

class GithubRepository(models.Model):
    _name = 'github.repository'
    _description = 'GitHub Repository'

    name = fields.Char(string='Repository Name', required=True)
    owner = fields.Char(string='Owner (User/Organization)', required=True)
    html_url = fields.Char(string='GitHub URL', readonly=True)
    last_sync_date = fields.Datetime(string='Last Sync Date', readonly=True)
    app_ids = fields.One2many('github.app', 'repository_id', string='Odoo Apps')

    def _get_github_headers(self):
        # Fetch PAT securely from system parameters or a dedicated config model
        param = self.env['ir.config_parameter'].sudo().get_param('odoo_github_integration.github_token')
        if not param:
            raise UserError("GitHub Personal Access Token not configured in system parameters.")
        return {
            "Authorization": f"token {param}",
            "Accept": "application/vnd.github.v3+json"
        }

    def _get_github_api_url(self, endpoint):
        return f"https://api.github.com/{endpoint}"

    def sync_repository_data(self):
        headers = self._get_github_headers()
        for repo in self:
            _logger.info(f"Syncing repository: {repo.owner}/{repo.name}")
            try:
                # Fetch repository details to ensure it exists and get updated info
                repo_detail_url = self._get_github_api_url(f"repos/{repo.owner}/{repo.name}")
                response = requests.get(repo_detail_url, headers=headers)
                response.raise_for_status()
                repo_data = response.json()

                repo.write({
                    'html_url': repo_data.get('html_url'),
                    'last_sync_date': fields.Datetime.now(),
                })

                # Find and update Odoo apps
                self._find_and_update_odoo_apps(repo)

            except requests.exceptions.RequestException as e:
                _logger.error(f"Error syncing repository {repo.owner}/{repo.name}: {e}")
                self.env.user.notify_warning(f"Error syncing repository {repo.owner}/{repo.name}: {e}")
            except Exception as e:
                _logger.error(f"An unexpected error occurred during sync for {repo.owner}/{repo.name}: {e}")
                self.env.user.notify_warning(f"An unexpected error occurred during sync for {repo.owner}/{repo.name}: {e}")

    def _find_and_update_odoo_apps(self, repo):
        headers = self._get_github_headers()
        branch = 'master' # Or retrieve from a field on the repo record if you support multiple branches
        current_app_names = set(repo.app_ids.mapped('name'))
        found_app_names = set()

        try:
            tree_url = self._get_github_api_url(f"repos/{repo.owner}/{repo.name}/git/trees/{branch}?recursive=1")
            tree_response = requests.get(tree_url, headers=headers)
            tree_response.raise_for_status()
            tree = tree_response.json().get('tree', [])

            for item in tree:
                if item['type'] == 'blob' and item['path'].endswith('__manifest__.py'):
                    manifest_path = item['path']
                    module_name = manifest_path.split('/')[-2] # Get parent directory name as module name

                    # Fetch manifest content
                    content_url = self._get_github_api_url(f"repos/{repo.owner}/{repo.name}/contents/{manifest_path}")
                    content_response = requests.get(content_url, headers=headers)
                    content_response.raise_for_status()
                    content_data = content_response.json().get('content')

                    if content_data:
                        try:
                            decoded_content = base64.b64decode(content_data).decode('utf-8')
                            manifest_dict = eval(decoded_content) # Be careful: `eval` is dangerous if input is untrusted
                            # A safer alternative is to parse it manually or use a dedicated manifest parser if available

                            app_version = manifest_dict.get('version', 'N/A')
                            app_name = manifest_dict.get('name', module_name) # Use manifest name if available

                            app_vals = {
                                'name': app_name,
                                'module_name': module_name, # Store original folder name
                                'version': app_version,
                                'path': manifest_path,
                                'repository_id': repo.id,
                            }

                            existing_app = self.env['github.app'].search([
                                ('repository_id', '=', repo.id),
                                ('module_name', '=', module_name)
                            ], limit=1)

                            if existing_app:
                                existing_app.write(app_vals)
                                _logger.info(f"Updated app: {app_name} ({app_version}) in {repo.name}")
                            else:
                                self.env['github.app'].create(app_vals)
                                _logger.info(f"Created new app: {app_name} ({app_version}) in {repo.name}")
                            found_app_names.add(module_name)
                        except Exception as e:
                            _logger.warning(f"Could not parse manifest for {manifest_path}: {e}")
        except requests.exceptions.RequestException as e:
            _logger.error(f"Error fetching tree for {repo.owner}/{repo.name}: {e}")

        # Remove apps that are no longer present in the repository
        apps_to_remove = current_app_names - found_app_names
        if apps_to_remove:
            self.env['github.app'].search([
                ('repository_id', '=', repo.id),
                ('module_name', 'in', list(apps_to_remove))
            ]).unlink()
            _logger.info(f"Removed old apps from {repo.name}: {apps_to_remove}")


class GithubApp(models.Model):
    _name = 'github.app'
    _description = 'Odoo App in GitHub Repository'

    name = fields.Char(string='App Name', required=True)
    module_name = fields.Char(string='Module Folder Name', required=True) # Actual folder name on GitHub
    version = fields.Char(string='Version', required=True)
    path = fields.Char(string='Path in Repository', required=True)
    repository_id = fields.Many2one('github.repository', string='Repository', required=True, ondelete='cascade')