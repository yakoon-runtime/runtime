from collections.abc import Sequence

from yakoon.base.runtime.controllers import Controller


class ControllerDirectory:
    """
    Registry interface for routing commands to platform definitions.
    Used by the Engine to remain agnostic of domain structure.
    """

    def __init__(self):
        """
        Defines the interface for a registry that manages all
        available domain controllers.

        A domain registry is responsible for:
        - Providing access to all registered controllers (e.g. shell, office)
        - Resolving controllers by their unique ID
          (used in routing, command dispatch, etc.)

        This interface is typically implemented by the system shell or platform
        entrypoint to coordinate domain activation, switching, and global
        command handling.
        """

        self._controllers: dict[str, Controller] = {}

    def register(self, controllers: list[Controller]):
        has_shell, shell_id = False, None
        for controller in controllers:
            if controller.id in self._controllers:
                raise ValueError(
                    f"Duplicate controller names detected: {controller.id}"
                )
            if controller.is_shell and has_shell:
                raise ValueError(
                    f"Duplicate shell controller: {shell_id.id} / {controller.id}"  # type: ignore
                )
            if controller.is_shell:
                has_shell = True
                shell_id = controller.id
            self._controllers[controller.id] = controller

        if not has_shell:
            raise ValueError("No shell controller found")

    def find_shell(self) -> Controller | None:
        for controller in self._controllers.values():
            if controller.is_shell:
                return controller

    def get(self, controller_id: str) -> Controller | None:
        """
        Resolves and returns a domain controller by its unique ID.

        Args:
            id (str): The identifier of the domain controller (e.g. 'shell', 'office').

        Returns:
            Controller: The matching controller instance.
        """

        return self._controllers.get(controller_id)

    def get_all(self) -> Sequence[Controller]:
        """
        Returns all registered domain controllers.

        Returns:
            list[Controller]: A list of all available domain controllers.
        """

        return list(self._controllers.values())

    def has(self, controller_id: str) -> bool:
        """
        Returns true if controller has given id.

        Returns:
            bool: True if controller has given id.
        """

        return bool(self._controllers.get(controller_id, {}))
