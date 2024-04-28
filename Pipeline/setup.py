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
        "sentence_transformers",
        "PyMuPDF",
        "bitsandbytes",
        "peft @ git+https://github.com/huggingface/peft.git",
        "accelerate @ git+https://github.com/huggingface/accelerate.git",
    ],
    dependency_links=[
        "git+https://github.com/huggingface/peft.git#egg=peft",
        "git+https://github.com/huggingface/accelerate.git#egg=accelerate",
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
