import os
import json
import validators
import canvasapi.upload

from canvasapi.util import combine_kwargs


class Uploader(canvasapi.upload.Uploader):
    """
    Upload a file to Canvas.
    """

    def __init__(
        self,
        requester,
        url,
        file_or_url: canvasapi.upload.FileOrPathLike | str,
        **kwargs,
    ):
        """
        :param requester: The :class:`canvasapi.requester.Requester` to pass requests through.
        :type requester: :class:`canvasapi.requester.Requester`
        :param url: The URL to upload the file to.
        :type url: str
        :param file: A file handler or path of the file to upload.
        :type file: :class:`os.PathLike` or str
        """
        if validators.url(file_or_url):
            self._using_url = True
            self._using_filename = False
        elif isinstance(file_or_url, (os.PathLike, str)):
            if not os.path.exists(file_or_url):
                raise IOError("File {} does not exist.".format(os.fspath(file_or_url)))
            self._using_filename = True
            self._using_url = False
        else:
            self._using_filename = False
            self._using_url = False

        self._requester = requester
        self.url = url
        self.file = file_or_url
        self.kwargs = kwargs

    def request_upload_token(self, file):
        """
        Request an upload token.

        :param file: A file handler pointing to the file to upload.
        :returns: True if the file uploaded successfully, False otherwise, \
            and the JSON response from the API.
        :rtype: tuple
        """
        if not self._using_url:
            self.kwargs["name"] = os.path.basename(file.name)
            self.kwargs["size"] = os.fstat(file.fileno()).st_size
        else:
            self.kwargs["url"] = file

        response = self._requester.request(
            "POST", self.url, _kwargs=combine_kwargs(**self.kwargs)
        )

        return self.upload(response, file)

    def upload(self, response, file):
        """
        Upload the file.

        :param response: The response from the upload request.
        :type response: dict
        :param file: A file handler pointing to the file to upload.
        :returns: True if the file uploaded successfully, False otherwise, \
            and the JSON response from the API.
        :rtype: tuple
        """
        response = response.json()
        if not response.get("upload_url"):
            raise ValueError("Bad API response. No upload_url.")

        if not response.get("upload_params"):
            raise ValueError("Bad API response. No upload_params.")

        kwargs = response.get("upload_params")

        response = (
            self._requester.request(
                "POST",
                use_auth=False,
                _url=response.get("upload_url"),
                file=file,
                _kwargs=combine_kwargs(**kwargs),
            )
            if not self._using_url
            else self._requester.request(
                "POST",
                use_auth=False,
                _url=response.get("upload_url"),
                _kwargs=combine_kwargs(**kwargs),
            )
        )

        # remove `while(1);` that may appear at the top of a response
        response_json = json.loads(response.text.lstrip("while(1);"))

        return ("url" in response_json, response_json)
