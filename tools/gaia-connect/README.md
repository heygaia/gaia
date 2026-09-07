# gaia-connect

Sync a local browser's logins to GAIA so its server-side browser stays signed in
for your tasks. Reads the browser's own encrypted cookies (one OS-keychain
prompt = your consent), lets you choose which sites to sync, and uploads them to
`POST /browser/import` with a single-use code.

macOS + Chromium family (Arc, Chrome, Helium, Brave, Edge) for now. Linux and
Windows detect but don't decrypt yet — the binary still builds and runs there.

## Users: run it via the CLI

Mint a single-use import code in GAIA → Settings → Browser → Import, then:

    npx @heygaia/cli connect --token <code>

`gaia connect` downloads the matching `gaia-connect` binary for your OS from the
`cli-v<version>` GitHub release, verifies its SHA-256, caches it in
`~/.gaia/bin/`, and forwards every flag below to it untouched.

## Interactive (from source)

    go run .            # or: ./gaia-connect
    # pick a browser → approve the keychain prompt → search/toggle sites → sync

`--api` defaults to `https://api.heygaia.io`. For dev or self-hosting pass
`--api http://localhost:8510`, where the import code is auto-minted (dev bypass)
so `--token` can be omitted.

## Robot mode (agents)

No TUI, flags in, JSON out — decoupled from the View for programmatic use:

    ./gaia-connect --json --list                       # {"browsers":[...]}
    ./gaia-connect --json --browser Arc --list         # {"sessions":[{site,cookies}]}
    ./gaia-connect --json --browser Arc --sites github.com,x.com --token CODE

`GAIA_CONNECT_JSON=1` also enables robot mode; `ACCESSIBLE=1` switches the
interactive form to its screen-reader-friendly renderer.
