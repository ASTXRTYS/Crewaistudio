from setuptools import setup, find_packages

setup(
    name="auren",
    version="0.1.0",
    package_dir={"auren": "src/auren"},
    packages=find_packages(where="src"),
    package_data={'auren': ['app/static/img/*']},
    install_requires=[
        "crewai>=0.8.0",
        "streamlit>=1.28.0",
        "pydantic>=2.0.0",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "python-telegram-bot>=20.0",
    ],
) 