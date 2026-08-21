"""Check that everything the Fab listing and the plugin descriptor link to resolves anonymously.

An anonymous 404 on a descriptor URL is a submission blocker for the plugin, and the same
standard applies to the links its description carries. Those links point at this repository, so
the check belongs here rather than in someone's memory.

The requests below carry no authentication of any kind, which is what makes the result mean what
it claims to mean.

    python cli/tools/check_public_urls.py
"""

import sys
import urllib.error
import urllib.request

REPOSITORY = "https://github.com/davbludev/JutsuUnrealMcpPublic"

#: Every page a buyer can arrive at from the listing or the descriptor.
URLS = (
    REPOSITORY,
    REPOSITORY + "/blob/main/README.md",
    REPOSITORY + "/blob/main/cli/README.md",
    REPOSITORY + "/issues",
)

TIMEOUT_SECONDS = 15


def check(url):
    request = urllib.request.Request(url, method="GET", headers={"User-Agent": "jutsu-mcp-cli"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return response.status, ""
    except urllib.error.HTTPError as failure:
        return failure.code, failure.reason
    except (urllib.error.URLError, OSError) as failure:
        return 0, str(failure)


def main():
    failures = 0
    for url in URLS:
        status, detail = check(url)
        if status == 200:
            print("  200  %s" % url)
        else:
            failures += 1
            print("  %-4s %s  %s" % (status or "down", url, detail))
    if failures:
        print("\n%d link(s) are not anonymously reachable. The listing must not ship until they "
              "are." % failures)
        return 1
    print("\nEvery linked page resolves for a logged-out visitor.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
