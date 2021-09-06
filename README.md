# Robot email forwarding

* Logs into a gmail account.
* Iterates over the inbox.
* Forwards to the email specified.
* Tracks state to pick up where it left off.
* Logs status for each message.

Using `Pipenv` for managing dependencies:

```
pip install pipenv
pipenv virtualenv 3.9.0 email_forwarder
pipenv activate email_forwarder
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