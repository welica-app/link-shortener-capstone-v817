"""Complete the three marked method bodies. Read STORAGE_GUIDE.md first.

Keep the class name, method names, inputs and returned shapes unchanged.
ProtectedStorage owns connections, transactions and redirect counting.
"""
from protected_storage import ProtectedStorage


class Store(ProtectedStorage):
    def create(self, code, destination):
        """Save a new link, returning True. Return False for an existing code.

        Use `with self.write() as connection:` for your lookup and insertion.
        Keep caller values separate from SQL text with ? placeholders.
        The links table gives a new row its initial click count.
        """
        raise NotImplementedError("Complete Store.create using CONTRACT.md")

    def resolve(self, client, code, now):
        """Return (302, destination), (404, None), or (429, None).

        Call self.accept_redirect(client, code, now) and return its result.
        That prepared method owns both row changes and their protection.
        Do not read or write either table separately in this method.
        """
        raise NotImplementedError("Complete Store.resolve using CONTRACT.md")

    def stats(self, code):
        """Return {code, destination, clicks}, or None for an absent code.

        Use `with self.read() as connection:` for a parameterised SELECT.
        This method reads saved values. It does not change a click count.
        """
        raise NotImplementedError("Complete Store.stats using CONTRACT.md")
