from setuptools import setup, find_packages

setup(
    name="company_intelligence_agent",
    version="0.1",
    packages=find_packages("src"),  # Only include modules inside `src`
    package_dir={"": "src"},        # Define `src` as the base directory
)