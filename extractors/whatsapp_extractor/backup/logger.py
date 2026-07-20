class Log:
    def __init__(self, verbose: bool, force: bool):
        self.verbose = verbose
        self.force = force

    def v(self, msg: str):
        if self.verbose:
            print(f"[V] {msg}")

    @staticmethod
    def i(msg: str):
        print(f"[I] {msg}")

    def e(self, msg: str):
        print(f"[E] {msg}")
        if not self.force:
            print('To bypass checks, use the "--force" parameter')
            exit(1)

    @staticmethod
    def f(msg: str):
        print(f"[F] {msg}")
        exit(1)
