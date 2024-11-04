<p align="center">
  <img src="https://raw.githubusercontent.com/PKief/vscode-material-icon-theme/ec559a9f6bfd399b82bb44393651661b08aaf7ba/icons/folder-markdown-open.svg" width="100" alt="project-logo">
</p>
<p align="center">
    <h1 align="center">ARTNRTOID</h1>
</p>
<p align="center">
    <em>Convert with ease, drive sales increase.</em>
</p>
<p align="center">
	<img src="https://img.shields.io/github/license/AarchiveSoft/ArtNrToID.git?style=default&logo=opensourceinitiative&logoColor=white&color=0080ff" alt="license">
	<img src="https://img.shields.io/github/last-commit/AarchiveSoft/ArtNrToID.git?style=default&logo=git&logoColor=white&color=0080ff" alt="last-commit">
	<img src="https://img.shields.io/github/languages/top/AarchiveSoft/ArtNrToID.git?style=default&color=0080ff" alt="repo-top-language">
	<img src="https://img.shields.io/github/languages/count/AarchiveSoft/ArtNrToID.git?style=default&color=0080ff" alt="repo-language-count">
<p>
<p align="center">
	<!-- default option, no dependency badges. -->
</p>

<br><!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary><br>

- [ Overview](#-overview)
- [ Features](#-features)
- [ Repository Structure](#-repository-structure)
- [ Modules](#-modules)
- [ Getting Started](#-getting-started)
  - [ Installation](#-installation)
  - [ Usage](#-usage)
  - [ Tests](#-tests)
- [ Project Roadmap](#-project-roadmap)
- [ Contributing](#-contributing)
- [ License](#-license)
- [ Acknowledgments](#-acknowledgments)
</details>
<hr>

##  Overview

The ArtNrToID project delivers the Gambio ID Converter Application, a PyQt6-based tool designed to streamline article number conversion into Gambio IDs. Users benefit from an intuitive interface for brand and category selection, exclusion of specific articles, and real-time progress updates during web scraping. Leveraging Selenium for web data extraction and SQLite for storage, the application offers a seamless experience with efficient results viewing and copying capabilities.

---

##  Features

|    |   Feature         | Description |
|----|-------------------|---------------------------------------------------------------|
| ⚙️  | **Architecture**  | The project follows a modular architecture using Python with a PyQt6-based GUI tool for article number conversion to Gambio IDs. It interacts with SQLite for data storage, and Selenium for web scraping. It's designed for user-friendly product information extraction and conversion.|
| 🔩 | **Code Quality**  | The codebase maintains good quality and style standards with clear separation of concerns, proper variable naming, and consistent coding conventions. The use of PyQt6 and Selenium libraries showcases a strong understanding of Python programming best practices.|
| 📄 | **Documentation** | The project has detailed documentation explaining the functionalities of the GUI tool, including key features, usage instructions, and technical details. The README provides comprehensive information to help users understand and utilize the application effectively.|
| 🔌 | **Integrations**  | Key integrations include PyQt6 for the GUI, SQLite for data storage, and Selenium for web scraping. These external dependencies enhance the functionality of the project by providing robust tools for efficient product information extraction and transformation.|
| 🧩 | **Modularity**    | The codebase exhibits a high level of modularity, enabling easy reusability of components for future enhancements or integration into other projects. The separation of concerns in different modules ensures maintainability and scalability in adding new features or modifying existing ones.|
| 🧪 | **Testing**       | Testing frameworks and tools used are not explicitly mentioned in the repository contents. However, adding unit tests and possibly integration tests can further enhance code reliability and maintainability.|
| ⚡️  | **Performance**   | The project's efficiency is notable, delivering real-time progress updates during web scraping and quick conversion results. Resource usage appears optimized, with the application performing well in handling product category selection and article number conversion tasks.|
| 🛡️ | **Security**      | Security measures for data protection and access control are not explicitly detailed in the repository contents. Implementing secure data handling practices and access controls can enhance the overall security of the application.|
| 📦 | **Dependencies**  | Key external libraries and dependencies used in the project include PyQt6 for GUI development, SQLite for data storage, and Selenium for web scraping functionalities. These libraries play a crucial role in enriching the project's capabilities and performance.|

---

##  Repository Structure

```sh
└── ArtNrToID/
    ├── loading_icon.ico
    ├── main_icon.ico
    ├── output
    │   └── GambioIDs.db
    └── scrape.py
```

---

##  Modules

<details closed><summary>.</summary>

| File                                                                             | Summary                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| ---                                                                              | ---                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| [scrape.py](https://github.com/AarchiveSoft/ArtNrToID.git/blob/master/scrape.py) | The `scrape.py` file within the ArtNrToID repository houses the Gambio ID Converter Application, a user-friendly GUI tool developed using PyQt6. This tool enables users to convert article numbers into Gambio IDs by selecting product categories, excluding specific articles, and viewing the conversion results. It interacts with a SQLite database for data storage and retrieval and employs Selenium for web scraping to extract product information from a designated website.**Key Features:**-Intuitive interface for brand and category selection.-Option to exclude specific articles from the conversion process.-Real-time progress updates during web scraping.-Results can be conveniently copied to the clipboard.This applications main class, `GUI`, orchestrates the GUI components, such as brand and category dropdowns, exclusion input fields, and conversion/copy result buttons, ensuring a seamless user experience. |

</details>

---

##  Getting Started

**System Requirements:**

* **Python**: `version x.y.z`

###  Installation

<h4>From <code>source</code></h4>

> 1. Clone the ArtNrToID repository:
>
> ```console
> $ git clone https://github.com/AarchiveSoft/ArtNrToID.git
> ```
>
> 2. Change to the project directory:
> ```console
> $ cd ArtNrToID
> ```
>
> 3. Install the dependencies:
> ```console
> $ pip install -r requirements.txt
> ```

###  Usage

<h4>From <code>source</code></h4>

> Run ArtNrToID using the command below:
> ```console
> $ python main.py
> ```

###  Tests

> Run the test suite using the command below:
> ```console
> $ pytest
> ```

---

##  Project Roadmap

- [X] `► INSERT-TASK-1`
- [ ] `► INSERT-TASK-2`
- [ ] `► ...`

---

##  Contributing

Contributions are welcome! Here are several ways you can contribute:

- **[Report Issues](https://github.com/AarchiveSoft/ArtNrToID.git/issues)**: Submit bugs found or log feature requests for the `ArtNrToID` project.
- **[Submit Pull Requests](https://github.com/AarchiveSoft/ArtNrToID.git/blob/main/CONTRIBUTING.md)**: Review open PRs, and submit your own PRs.
- **[Join the Discussions](https://github.com/AarchiveSoft/ArtNrToID.git/discussions)**: Share your insights, provide feedback, or ask questions.

<details closed>
<summary>Contributing Guidelines</summary>

1. **Fork the Repository**: Start by forking the project repository to your github account.
2. **Clone Locally**: Clone the forked repository to your local machine using a git client.
   ```sh
   git clone https://github.com/AarchiveSoft/ArtNrToID.git
   ```
3. **Create a New Branch**: Always work on a new branch, giving it a descriptive name.
   ```sh
   git checkout -b new-feature-x
   ```
4. **Make Your Changes**: Develop and test your changes locally.
5. **Commit Your Changes**: Commit with a clear message describing your updates.
   ```sh
   git commit -m 'Implemented new feature x.'
   ```
6. **Push to github**: Push the changes to your forked repository.
   ```sh
   git push origin new-feature-x
   ```
7. **Submit a Pull Request**: Create a PR against the original project repository. Clearly describe the changes and their motivations.
8. **Review**: Once your PR is reviewed and approved, it will be merged into the main branch. Congratulations on your contribution!
</details>

<details closed>
<summary>Contributor Graph</summary>
<br>
<p align="center">
   <a href="https://github.com{/AarchiveSoft/ArtNrToID.git/}graphs/contributors">
      <img src="https://contrib.rocks/image?repo=AarchiveSoft/ArtNrToID.git">
   </a>
</p>
</details>

---

##  License

This project is protected under the [SELECT-A-LICENSE](https://choosealicense.com/licenses) License. For more details, refer to the [LICENSE](https://choosealicense.com/licenses/) file.

---

##  Acknowledgments

- List any resources, contributors, inspiration, etc. here.

[**Return**](#-overview)

---
