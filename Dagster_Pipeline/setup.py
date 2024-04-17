from setuptools import find_packages, setup

setup(
    name="sample_dagster",
    packages=find_packages(exclude=["sample_dagster_tests"]),
    install_requires=[
        "dagster",
        "dagster-cloud",
        "requests",
        "beautifulsoup4",
        "lxml",
        "selenium",
        "webdriver_manager",
        "pypdf",
        "fpdf",
        "langchain",
        "langchain_community",
        "chromadb",
        "sentence_transformers"
        
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
