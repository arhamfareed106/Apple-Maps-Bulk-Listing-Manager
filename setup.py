from setuptools import setup, find_packages

setup(
    name="apple-maps-manager",
    version="1.0.0",
    description="Apple Maps Bulk Listing Management System",
    author="Your Company",
    author_email="engineering@yourcompany.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    python_requires=">=3.9",
    install_requires=[
        "aiohttp>=3.8.0",
        "requests>=2.28.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "SQLAlchemy>=2.0.0",
        "asyncpg>=0.27.0",
        "psycopg2-binary>=2.9.0",
        "pandas>=1.5.0",
        "openpyxl>=3.0.0",
        "authlib>=1.2.0",
        "requests-oauthlib>=1.3.0",
        "tenacity>=8.2.0",
        "circuitbreaker>=1.4.0",
        "click>=8.1.0",
        "rich>=13.0.0",
        "tqdm>=4.64.0",
        "structlog>=22.0.0",
        "python-dotenv>=1.0.0",
        "pyyaml>=6.0.0",
        "cachetools>=5.3.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.2.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "test": [
            "pytest>=7.2.0",
            "pytest-asyncio>=0.21.0",
            "pytest-mock>=3.10.0",
            "httpx>=0.24.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "apple-maps-manager=src.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)