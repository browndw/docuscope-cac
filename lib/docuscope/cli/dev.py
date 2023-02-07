from docuscope._dev import build, propagate, tests


def dev_cli(subparsers):
    dev_parser = subparsers.add_parser("dev")
    dev_subparsers = dev_parser.add_subparsers(dest="dev")
    add_test_parser(dev_subparsers)
    add_propagate_parser(dev_subparsers)
    add_cypress_parser(dev_subparsers)
    add_clean_imports_parser(dev_subparsers)
    add_build_parser(dev_subparsers)

    return dev_parser


def add_test_parser(dev_subparsers):
    parser = dev_subparsers.add_parser("tests")
    parser.set_defaults(func=tests.run_tests)


def add_propagate_parser(dev_subparsers):
    parser = dev_subparsers.add_parser("propagate")

    parser.add_argument(
        "--update",
        help="Run poetry update first.",
        action="store_true",
    )

    parser.set_defaults(func=propagate.propagate_all)


def add_build_parser(dev_subparsers):
    parser = dev_subparsers.add_parser("build")

    parser.add_argument(
        "--install",
        help="Run yarn install first.",
        action="store_true",
    )

    parser.set_defaults(func=build.build_binary)


def add_cypress_parser(dev_subparsers):
    parser = dev_subparsers.add_parser("cypress")
    parser.set_defaults(func=tests.run_cypress)


def add_clean_imports_parser(dev_subparsers):
    parser = dev_subparsers.add_parser("imports")
    parser.set_defaults(func=tests.run_clean_imports)

