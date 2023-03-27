#!/usr/bin/env python3
"""
Naive ViUR3 project porting script with a simple search & replace mechanism using lookup table.
"""

import os, argparse, difflib

# Naive lookup table. Could be done better later...
lookup = {
    "BasicApplication": "SkelModule",
    "addItemSuccess": "addSuccess",
    "callDeferred": "CallDeferred",
    "editItemSuccess": "editSuccess",
    "from server import": "from viur.core import",
    "from server.bones import": "from viur.core.bones import",
    "getEmtpyValueFunc": "getEmptyValueFunc",
    "isLocalDevelopmentServer": "conf[\"viur.instance.is_dev_server\"]",
    "onItemAdded": "onAdded",
    "onItemDeleted": "onDeleted",
    "onItemEdited": "onEdited",
    "projectID": "conf[\"viur.instance.project_id\"]",
    "utils.currentLanguage": "current.language",
    "utils.currentRequest": "current.request",
    "utils.currentRequestData": "current.request_data",
    "utils.currentSession": "current.session",
    "utils.getCurrentUser": "current.user.get",
    "utils.isLocalDevelopmentServer": "conf[\"viur.instance.is_dev_server\"]",
    "utils.projectID": "conf[\"viur.instance.project_id\"]",
}

bones = [
    "base",
    "boolean",
    "captcha",
    "color",
    "credential",
    "date",
    "email",
    "file",
    "key",
    "numeric",
    "password",
    "randomSlice",
    "raw",
    "record",
    "relational",
    "selectCountry",
    "select",
    "sortindex",
    "spatial",
    "string",
    "text",
    "treeLeaf",
    "treeNode",
    "user"
]

lookup.update({
    f"{name}Bone": f"{name[0].upper()}{name[1:]}Bone" for name in bones
})


def make_2to3(args, filename):
    """
    Performs the conversion on a file with the provided options.
    """
    with open(filename, "r") as f:
        original_content = content = f.read()

    count = 0
    for k, v in lookup.items():
        if k in content:
            content = content.replace(k, v)
            count += 1

    if count:
        if not args.dryrun:
            if not args.daredevil:
                os.rename(filename, filename + ".bak")

            with open(filename, "w") as f:
                f.write(content)

            print("Modified %r" % filename)
        else:
            print(
                "\n".join(
                    difflib.unified_diff(
                        original_content.splitlines(),
                        content.splitlines(),
                        filename,
                        filename
                    )
                )
            )


def main():
    # Get arguments
    ap = argparse.ArgumentParser(
        description="ViUR3 porting tool"
    )

    ap.add_argument(
        "path",
        type=str,
        help="Path to file or folder"
    )

    ap.add_argument(
        "-d", "--dryrun",
        action="store_true",
        help="Dry-run for testing, don't modify files"
    )
    ap.add_argument(
        "-x", "--daredevil",
        action="store_true",
        help="Don't make backups of files, just replace and deal with it"
    )

    args = ap.parse_args()

    if os.path.isfile(args.path):
        make_2to3(args, args.path)
    else:
        assert os.path.isdir(args.path), f"The path {args.path!r} is invalid!"

        # Iterate all files in current folder
        for root, dirs, files in os.walk(args.path):
            # Ignore ViUR library folders
            if any(ignore in root for ignore in ["viur", "flare", "html5"]):
                continue

            for filename in files:
                # Ignore anything without a .py-extension
                ext = os.path.splitext(filename)[1].lower()[1:]
                if ext not in ["py"]:
                    continue

                make_2to3(args, os.path.join(root, filename))


if __name__ == "__main__":
    main()
