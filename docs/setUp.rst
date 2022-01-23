.. _settingup:

Setting up your environment
============================

| First of all, for the initial setup, we invite you to look at the |anki developer web page|.
| You will find explanations about installation and also some SDK examples or documentation around the Cozmo's library.
|

-----------

"""""""""""""""""""
Flask installation
"""""""""""""""""""
You will need to install this library to run the server for user interface, type the following into the Terminal window::

    pip3 install flask

"""""""""""""""""""
Numpy installation
"""""""""""""""""""
You will need to install this library to convert image in a numpy array to perform fingers detection, type the following into the Terminal window::

    pip3 install numpy

""""""""""""""""""""
Pillow installation
""""""""""""""""""""
You will need to install this library to mirror cozmo's image, type the following into the Terminal window::

    pip3 install pillow

"""""""""""""""""""""""
Mediapipe installation
"""""""""""""""""""""""
You will need to install this library to perform hand landmarks, type the following into the Terminal window::

    pip3 install mediapipe

"""""""""""""""""""""""
Requests installation
"""""""""""""""""""""""
You will need to install this library to allow sending information from user interface to Cozmo, type the following into the Terminal window::

    pip3 install requests

|






.. |anki developer web page| raw:: html

   <a href="http://cozmosdk.anki.com/docs/initial.html" target="_blank">Anki developer web page</a>