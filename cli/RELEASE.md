# Releasing the CLI

The CLI ships from this repository and nothing about it is uploaded to Fab. The Fab listing and
the plugin descriptor link here, so what a release has to guarantee is that the link resolves for
a logged-out visitor and that what they find runs.

## What a release is

A git tag on `main`, named `cli-vMAJOR.MINOR.PATCH`. There is no archive artefact: a clone or
GitHub's own source download is the delivery, and the tree at the tag is the release. `cli/`
carries its own version in `cli/jutsu_mcp/__init__.py`; bump it in the commit being tagged.

There is no compatibility matrix to maintain. The CLI declares no tool names, no schemas and no
registry version, so it stays compatible across plugin versions by construction. Say that in the
README rather than tracking it.

## Before tagging

All of these have to pass. The first two need nothing installed; the rest need an Unreal editor
running with the plugin enabled, and the last also needs Node.

```
python cli/tools/check_cli_vocabulary.py
python -m unittest discover -s cli/tests
python cli/tools/check_cli_forwarding.py --port <editor port>
python cli/tests/check_live_transport.py --port <editor port>
python cli/tools/check_public_urls.py
cd cli/tests/client-compatibility && npm ci && npm test
```

Then walk the README's quickstart literally, on an account that has never run the CLI, using an
interpreter chosen the way the README tells a buyer to choose one. A quickstart that only works
because of something already on the developer's machine is the failure this step exists to catch.

## Anonymous reachability

`Docs/FAB_PREPARATION_PLAN.md` in the plugin repository records that an anonymous 404 on a
descriptor URL is a submission blocker. The same standard applies to every link the listing
description carries, and the links point here, so the check lives here:
`cli/tools/check_public_urls.py` fetches each of them with no credentials and fails on anything
other than 200.

Run it from a machine that is not signed in to GitHub, or accept that the tool sends no
authentication of its own and treat that as equivalent.

## What this repository must not become

Fab factors the content of a linked page into the tags applied to the product. A source
repository raises nothing, which is precisely why unrelated material must not accumulate here.
