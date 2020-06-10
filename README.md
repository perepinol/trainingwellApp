<!--
*** Thanks for checking out this README Template. If you have a suggestion that would
*** make this better, please fork the repo and create a pull request or simply open
*** an issue with the tag "enhancement".
*** Thanks again! Now go create something AMAZING! :D
-->





<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->



<!-- TABLE OF CONTENTS -->
## Table of Contents

* [About the Project](#about-the-project)
  * [Built With](#built-with)
* [Getting Started](#getting-started)
  * [Prerequisites](#prerequisites)
* [Usage](#usage)
* [Roadmap](#roadmap)
* [Contributing](#contributing)
* [License](#license)
* [Contact](#contact)



<!-- ABOUT THE PROJECT -->
## About The Project

Trainingwell app consists of an easy way of booking and hiring sports spaces and fields for an organizer purpose. This project helps out those who want to reserve a space to perform an activity, the assistants invited to an event, and the facility responsible and the enterprise manager for their business.

The application allows to check current and incoming event information, make a reservation, manage the spaces and incidences and generate some reports based on the income and space usage. The system also generates the invoice of a reservation and stores it up to 2 years for legal purpouses.

### Built With
The application is build with Python language for the backend and using the following frameworks:
* [Bootstrap](https://getbootstrap.com)
* [JQuery](https://jquery.com)
* [Django](https://www.djangoproject.com/)
* [SQLite](https://www.sqlite.org)



<!-- GETTING STARTED -->
## Getting Started

### Prerequisites

Obviously, at least Python3 is needed.

All other requisites are included in the requirements.txt file. To install them, we strongly suggest you to use a IDE which does it automatically or use a virtual environment (Pipenv).

```sh
pipenv install [-r path/to/requirements.txt]
```
This will create the Pipfile and install the dependencies.


<!-- USAGE EXAMPLES -->
## Usage

It is strongly recommended to use any software which works with django automatically. Otherwise, you should use the following terminal comands to run the server.

```sh
python3 manage.py runserver
python3 manage.py makemigrations eventApp
python3 manage.py migrate eventApp
python3 manage.py makemigrations
python3 manage.py migrate
```

Note that the migrations must be done either using an IDE or manually in terminal.


<!-- ROADMAP -->
## Roadmap

This project is divided in three sprints or plannings, each of them focused on one major feature.

See the [issues](https://github.com/perepinol/trainingwellApp/wiki) for a further information.


<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to be learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request


<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE` for more information.



<!-- CONTACT -->
## Contact

Project Link: [https://github.com/perepinol/trainingwellApp/](https://github.com/perepinol/trainingwellApp/)


