from setuptools import setup, find_packages, find_namespace_packages

setup(
    package_dir={'': 'src'},
    packages=find_namespace_packages(where='src'),
    include_package_data=True,
    package_data = {
        'pyri.webui_browser.panels': ['*.html'],
        'pyri.webui_browser.components': ['*.html'],
        'pyri.webui_browser': ['*.html']
    },
    zip_safe=False
)