"""
ApiKeyAJM.py

Provides a way to read/manage API keys.
"""
import json
from logging import getLogger
from pathlib import Path
from typing import Optional, Union
import requests
import validators


class _BaseAPIKey:
    """
    APIKey is a class that provides a way to read/manage API keys. It has the following methods:
    __init__(self, **kwargs):
        Initializes an instance of the APIKey class. It takes optional keyword arguments:
        - logger: The logger to be used for logging messages. If not provided, a dummy logger will be used.
        - api_key: The API key to be used. If not provided, it will try to get the key from api_key_location.
        - api_key_location: The location of the file containing the API key. If not provided, it will use the DEFAULT_KEY_LOCATION.
    API_KEY(cls, **kwargs):
        This is a class method that returns an instance of the APIKey class with the provided keyword arguments.
        It takes the same keyword arguments as __init__ and returns the api_key property of the created instance.
    _key_file_not_found_error(self):
        This is a private method that raises a FileNotFoundError with a specified error message.
        It is called when the key file is not found.
    _get_api_key(self, key_location: Optional[Union[Path, str]] = None):
        This is a private method that gets the API key from the specified location.
        It takes an optional argument 'key_location' which can be a Path or a string.
        If key_location is not provided, it will use the api_key_location property of the instance.
        If the file is found, it reads the key from the file and sets it as the api_key property of the instance.
        If the file is not found or there is an IOError, it raises the appropriate exception.
    Note:
    - The DEFAULT_KEY_LOCATION property of the APIKey class can be set to the default location of the API key file.
    - The logger property is optional but it is recommended to provide a custom logger for logging purposes.
    - The APIKey class must be instantiated before accessing the api_key property.
    Example Usage:
        apiKey = APIKey(logger=myLogger, api_key_location='path/to/api_key.txt')
        key = apiKey.api_key
    """
    DEFAULT_KEY_LOCATION = None
    DEFAULT_LOGGER_NAME = 'dummy_logger'

    def __init__(self, **kwargs):
        # self._is_file_key = kwargs.get('is_file_key', True)
        self._initialize_logger(kwargs.get('logger'))
        self.api_key = kwargs.get('api_key')

        if not self.api_key:
            self._prep_for_fetch()
            self.api_key = self._fetch_api_key()

        self.logger.info(f"{self.__class__.__name__} Initialization complete.")

    def _initialize_logger(self, logger):
        """
        Initializes the logger for the software developer.

        :param logger: (Optional) The logger object to be used for logging.
        :return: None
        """
        self.logger = logger or getLogger(self.DEFAULT_LOGGER_NAME)

    def _prep_for_fetch(self):
        """
        This function is a private method that prepares the object for fetching data.
            It is intended to be implemented by a subclass.

        Raises:
            NotImplementedError: This exception is raised to indicate that the method
                is meant to be implemented by a subclass.
        """
        raise NotImplementedError("this is meant to be implemented by a subclass")

    @classmethod
    def get_api_key(cls, **kwargs):
        """
        This method is a class method in the given software. It returns the API key based on the provided arguments.

        Parameters:
        - kwargs: A variable number of keyword arguments that can be passed to the class constructor.
            These arguments are used to create an instance of the class.

        Returns:
        - The API key value generated by creating an instance of the class with the provided keyword arguments.

        """
        return cls(**kwargs).api_key

    def _fetch_api_key(self, **kwargs):
        """
        This method is a helper function that retrieves the API key needed for making API requests.
        It is marked as abstract and is intended to be implemented by a subclass of the current class.

        Parameters:
        - kwargs: Additional keyword arguments (optional)

        Raises:
        - NotImplementedError: If this method is not implemented by a subclass

        Returns:
        - None
        """
        raise NotImplementedError("this is meant to be implemented by a subclass")


class APIKeyFromFile(_BaseAPIKey):
    """
    This module provides the `APIKeyFromFile` class, which is used for fetching API keys from a file.

    Classes:
        - APIKeyFromFile: A class for fetching API keys from a file.

    Properties:
        - file_mode: A property that returns the file mode of the API key file.

    Methods:
        - __init__: The constructor method for the APIKeyFromFile class.
        - _prep_for_fetch: A private method that prepares the API key file for fetching.
        - _ensure_key_location_is_set: A private method that ensures the key location is set.
        - _raise_key_file_not_found_error: A private method that raises an error if the key file is not found.
        - _fetch_api_key: A private method that fetches the API key from the key file.

    Usage:
        To use this module, create an instance of the `APIKeyFromFile` class and call its methods as needed.
    """
    VALID_FILE_MODES = ['text', 'json']
    DEFAULT_FILE_MODE = 'text'

    def __init__(self, **kwargs):
        self.api_key_location = Path(kwargs.get('api_key_location'))
        if self.api_key_location.suffix == '.json':
            self._file_mode = 'json'
        elif self.api_key_location.suffix == '.txt':
            self._file_mode = 'text'
        else:
            self.logger.warning(f'File extension for {self.api_key_location} is not .json or .txt. '
                                f'Assuming {self.DEFAULT_FILE_MODE} file mode if file_mode not provided.')
        self._file_mode = kwargs.get('file_mode', self.DEFAULT_FILE_MODE)
        self._json_key = kwargs.get('json_key')
        super().__init__(**kwargs)

    @property
    def file_mode(self):
        if self._file_mode and self._file_mode in self.VALID_FILE_MODES:
            if (self._file_mode == 'json'
                    and self.api_key_location.suffix.split('.')[-1] != self._file_mode):
                self.logger.warning(f"File mode and file path suffix do not match, "
                                    f"({self.api_key_location.suffix.split('.')[-1]} and {self._file_mode}) "
                                    f"this could cause issues.")
            return self._file_mode

    def _prep_for_fetch(self):
        """
        This method is used to prepare for fetching data.
        It internally calls the `_ensure_key_location_is_set()`
        method to ensure that the key location is set before fetching the data.

        """
        self._ensure_key_location_is_set()

    def _ensure_key_location_is_set(self):
        """
        Ensures that the API key location is set.

        If the `api_key_location` attribute is not provided, it checks if the `DEFAULT_KEY_LOCATION` attribute is set.
        If the `DEFAULT_KEY_LOCATION` attribute is not set, it raises an `AttributeError` indicating
        that the `api_key_location` or `api_key` were not provided and `DEFAULT_KEY_LOCATION` is not set.

        This method is called internally to make sure that the API key location is set before making any API calls.
        """
        if not self.api_key_location:
            if not self.DEFAULT_KEY_LOCATION:
                raise AttributeError('api_key_location or api_key were not provided '
                                     'and DEFAULT_KEY_LOCATION not set.')

            self.api_key_location = self.DEFAULT_KEY_LOCATION

    def _raise_key_file_not_found_error(self):
        """
        This method is a private method that is called when a key file is not found.
        It raises a FileNotFoundError and logs the error message using the logger. The exception is then re-raised.
        """
        try:
            raise FileNotFoundError('key file not found')
        except FileNotFoundError as e:
            self.logger.error(e, exc_info=True)
            raise e

    def _fetch_api_key(self, key_location: Optional[Union[Path, str]] = None, **kwargs):
        """
        This method is responsible for fetching the API key from a specified location.

        Parameters:
        - key_location: Optional parameter that specifies the location of the API key file.
            It can be either a Path object or a string representing the file path.
            If not provided, the method will try to use the value of the 'api_key_location' property instead.

        Returns:
        - The API key string if the file is successfully read and its contents are parsed according to the specified
            file mode (either 'text' or 'json'). If the file mode is 'json' and a specific json key is set,
            only the value associated with that key will be returned.
            If the file cannot be found or read, None will be returned.

        Raises:
        - IOError: If there is an error while trying to read the file or if the file does not exist.

        Note:
        - This method is internally used by the class and should not be called directly."""
        if key_location and Path(key_location).is_file():
            key_path = key_location
        elif self.api_key_location and Path(self.api_key_location).is_file():
            key_path = self.api_key_location
        else:
            self._raise_key_file_not_found_error()
            return None

        try:
            with open(key_path, 'r') as f:
                if self.file_mode == 'text':
                    return f.read().strip()
                elif self.file_mode == 'json':
                    if self._json_key:
                        return json.load(f)[self._json_key]
                    return json.load(f)
        except IOError as e:
            self.logger.error(e, exc_info=True)
            raise e


class RemoteAPIKey(_BaseAPIKey):
    """
    This module contains a class `RemoteAPIKey` that represents a remote API key.
        It provides methods for fetching and validating the API key from a remote server.

    Class: RemoteAPIKey
        Inherits: _BaseAPIKey

    Methods:
        - __init__(self, base_url: str, create_key_endpoint: str, **kwargs)
            Initializes a new instance of the RemoteAPIKey class.
            Parameters:
                - base_url (str): The base URL of the remote server.
                - create_key_endpoint (str): The API endpoint for creating a new API key.
                - **kwargs: Additional keyword arguments.
            Returns: None

        - _construct_full_url(self) -> str
            Constructs the full URL for the API endpoint using the base URL and create key endpoint.
            Returns: The full URL as a string.

        - validated_base_url(self) -> str
            Validates the base URL and returns it.
            Returns: The validated base URL as a string.

        - _prep_for_fetch(self)
            Prepares for fetching the API key. This method is currently empty and does nothing.
            Returns: None

        - _fetch_api_key(self, username: str, password: str) -> str
            Fetches the API key from the remote server using the provided username and password.
            Parameters:
                - username (str): The username for authentication.
                - password (str): The password for authentication.
            Returns: The fetched API key as a string.

        - get_api_key(cls, **kwargs)
            Class method that returns an instance of RemoteAPIKey with the provided kwargs and calls its api_key property.
            If 'username' or 'password' are not provided as kwargs, an AttributeError is raised.
            Parameters:
                - **kwargs: Additional keyword arguments.
            Returns: The API key as a string.
    """
    JSON_CONTENT_TYPE = 'application/json'

    def __init__(self, base_url: str, create_key_endpoint: str, **kwargs):
        self._base_url = base_url
        self._create_key_endpoint = create_key_endpoint
        self._full_url = self._construct_full_url()

        username = kwargs.get('username')
        password = kwargs.get('password')

        # Inline the logic of assigning api_key
        self.api_key = None if not username or not password else self._fetch_api_key(username, password)
        if isinstance(self.api_key, dict):
            self.api_key = self.api_key.get('api_key')

        super().__init__(api_key=self.api_key, **kwargs)

    def _construct_full_url(self) -> str:
        """
        Constructs the full URL for the API endpoint.

        Returns:
            str: The constructed full URL.

        """
        return f'{self.validated_base_url}/{self._create_key_endpoint}'

    @property
    def validated_base_url(self) -> str:
        """
        A property that returns the validated base URL.

        Returns:
            str: The validated base URL.

        Raises:
            ValidationError: If the base URL is invalid.

        Note:
            The base URL is validated using the `validators` module. If the base URL is a non-empty string
            and it is not a valid URL, a `ValidationError` is raised. Otherwise, the base URL is returned,
            or None if it is empty.
        """
        if self._base_url and not validators.url(self._base_url):
            raise validators.ValidationError("Invalid URL")
        return self._base_url or None

    def _prep_for_fetch(self):
        """
        This method prepares the object for fetching data.
        """
        pass

    # noinspection PyMethodOverriding
    def _fetch_api_key(self, username: str, password: str) -> str:
        """
        Fetches the API key using the provided username and password.

        :param username: The username to authenticate with.
        :type username: str
        :param password: The password to authenticate with.
        :type password: str
        :return: The API key.
        :rtype: str
        :raises ConnectionError: If there is a connection error.
        :raises RequestException: If the request fails.
        """
        try:
            response = requests.post(
                url=self._full_url,
                json={'username': username, 'password': password},
                headers={'Content-Type': self.JSON_CONTENT_TYPE}
            )
            if response.ok:
                return response.json()
            raise requests.exceptions.RequestException(response.text)
        except requests.exceptions.ConnectionError as e:
            raise requests.exceptions.ConnectionError(e) from None

    @classmethod
    def get_api_key(cls, **kwargs):
        """
        Class Method `get_api_key`

        Get the API key for the specified user by authenticating with a username and password.

        Parameters:
            kwargs (dict): A dictionary of keyword arguments.
                username (str): The username of the user.
                password (str): The password of the user.

        Returns:
            str: The API key for the user.

        Raises:
            AttributeError: If the `username` or `password` parameter is not provided in `kwargs`.
        """
        if not kwargs.get('username') or not kwargs.get('password'):
            raise AttributeError('username or password were not passed in as kwargs')
        return cls(**kwargs).api_key


if __name__ == '__main__':
    # username = 'andrew'
    # password = '<PASSWORD>'
    test_attrs = {'base_url': 'http://127.0.0.1:5000',
                  'create_key_endpoint': 'get_api_key',
                  'username': 'andrew',
                  'password': '<PASSWORD>'}
    remote_api_key = RemoteAPIKey(** test_attrs)#.get_api_key(** test_attrs)
    #print(remote_api_key.api_key)
    print(remote_api_key.api_key)
