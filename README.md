# Robot email forwarding

* Logs into a gmail account.
* Iterates over the inbox.
* Forwards to the email specified.
* Tracks state to pick up where it left off.
* Logs status for each message.

Using `pipenv` for managing dependencies and `pyenv` for managing virtual environments:

```
pip install pipenv
pyenv virtualenv 3.9.0 email_forwarder
pyenv activate email_forwarder
pipenv install
```


Add a `.env` file that looks something like this:

```
EMAIL=youraddress@gmail.com 
PW=y0VrP@s$w0rd
FWD=afriend@zendesk.com
```

Run it:

```
./email
```