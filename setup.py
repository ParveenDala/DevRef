from setuptools import setup, find_packages

setup(
    name="devref",
    version="0.1.0",
    description="DevRef : Learn while you fix",
    author="Parveen",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "flask",
        "flask-cors",
        "httpx",
        "pydantic",
        "sentence-transformers",
        "pyyaml"
    ],
    python_requires=">=3.9",
    include_package_data=True,
    zip_safe=False,
)
