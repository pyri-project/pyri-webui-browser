from setuptools import setup, find_packages, find_namespace_packages

setup(
    name='pyri-webui-browser',
    version='0.1.0',
    description='PyRI Teach Pendant WebUI Browser Core',
    author='John Wason',
    author_email='wason@wasontech.com',
    url='http://pyri.tech',
    package_dir={'': 'src'},
    packages=find_namespace_packages(where='src'),
    include_package_data=True,
    package_data = {
        'pyri.webui_browser.panels': ['*.html']
    },
    zip_safe=False,
    install_requires=[
        'pyri-common',        
        'importlib-resources',        
    ],
    entry_points = {
        'pyri.plugins.webui_browser_panel': ['pyri-webui-browser=pyri.webui_browser.panels.standard_panels:get_webui_browser_panel_factory'],
    }
)