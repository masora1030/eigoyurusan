"""The setup script."""
from __future__ import absolute_import
from __future__ import unicode_literals

import setuptools

with open('README.md') as readme_file:
    readme = readme_file.read()


requirements = ['Click>=7.0',
                'setuptools',
                'pdfminer',
                'selenium',
                'arxiv',
                'markdown']

setuptools.setup(
    name="eigoyurusan",
    version="0.1.5",
    author="Sora Takashima",
    author_email="soraemonpockt@gmail.com",
    description="English is too difficult for me.",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/masora1030/eigoyurusan",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        "Intended Audience :: Education",
        "Topic :: Text Processing :: Linguistic",
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS",
    ],
    install_requires=requirements,
    license="MIT license",
    keywords="eigoyurusan, translate, translator, paper, PDF",
    project_urls={
        "Projects": "https://github.com/users/masora1030/projects/1",
        "Source": "https://github.com/masora1030/eigoyurusan",
    },
    entry_points="""
          # -*- Entry points: -*-
          [console_scripts]
          eigoyurusan = eigoyurusan.eigoyurusan:main
        """,
)