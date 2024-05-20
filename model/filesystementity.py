from os import sep, path
from time import localtime, strftime

TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S"

SIZE_UNITS = {
    0: "B",
    1: "KB",
    2: "MB",
    3: "GB",
    4: "TB",
    5: "PB",
    6: "EB",
}

class FilesystemEntity:
    __slots__ = ("full_path", "created_at", "depth", "children")
    full_path: str
    created_at: int
    last_modified: int
    children: list

    def __init__(self, full_path: str, created_at: int = None, depth: int = None, children: list = None):
        assert path.exists(full_path), "The full_path provided does not exist on the disk."
        self.full_path = full_path
        self.created_at = created_at
        self.depth = depth
        if not self.depth:
            self.depth = len(full_path.split(sep))
        self.children = children
        if not isinstance(self.children, list):
            self.children = []

    def add_child(self, child_entity):
        """Add a child entity to this FilesystemEntity's children.
        Raises an exception if this entity is not a directory, or if the provided child_entity does not have the correct type."""
        if not self.is_dir():
            raise TypeError("Cannot add child entity to a non-directory filesystem object.")
        if not isinstance(child_entity, FilesystemEntity):
            raise ValueError("child_entity must have type FilesystemEntity.")
        self.children.append(child_entity)

    def get_name(self):
        """Returns the name of this file or directory."""
        return self.full_path.split(sep)[-1]

    def get_parent_path(self):
        """Returns the full path to this entity's parent directory as a string."""
        return sep.join(self.full_path.split(sep)[:-1])

    def is_dir(self):
        """Returns true if this entity represents a directory / folder, else false."""
        return path.isdir(self.full_path)

    def get_size(self):
        """Get the storage size of this entity in bytes. If this entity is a directory, returns the sum size of its children."""
        size = path.getsize(self.full_path)
        if self.is_dir() and self.children:
            size = sum([c.get_size() for c in self.children])
        return size

    def get_last_modified(self):
        """Returns the last modified epoch timestamp of this entity. If this entity is a directory, returns the maximum last modified
        timestamp from its child entities."""
        last_modified = path.getmtime(self.full_path)
        if not self.is_dir() or not self.children:
            return last_modified
        max_child_mtime = max([c.get_last_modified() for c in self.children])
        return max(max_child_mtime, last_modified)

    def get_created_timestamp(self):
        return strftime(TIMESTAMP_FORMAT, localtime(self.created_at))

    def get_modified_timestamp(self):
        return strftime(TIMESTAMP_FORMAT, localtime(self.get_last_modified()))

    def get_size_rounded(self):
        """Returns a string representation of the entity size in B/KB/MB/GB"""
        size = self.get_size()
        div_count = 0
        while (dividend := size/1000) >= 1.0 and div_count <= max(SIZE_UNITS.keys()):
            size = dividend
            div_count += 1
        size_str = "{:.2f}".format(size)
        return f"{size_str} {SIZE_UNITS.get(div_count)}"


    def get_all_children_flattened(self):
        """Returns all children, and children's children, etc., recursively in a flattened list."""
        # Return empty if this is not a directory
        if not self.is_dir():
            return []
        # Start with a copy of children list
        child_list = self.children.copy()
        for child in self.children:
            child_list.extend(child.get_all_children_flattened())
        return child_list

    def to_dict(self):
        """Returns a dictionary reprsentation of this FilesystemEntity"""
        return {
            "name" : self.get_name(),
            "fullPath" : self.full_path,
            "size" : self.get_size(),
            "roundedSize" : self.get_size_rounded(),
            "depth": self.depth,
            "lastModified" : self.get_modified_timestamp(),
            "created" : self.get_created_timestamp(),
            "isDir" : self.is_dir(),
            "numChildren" : len(self.children),
            "children": [c.to_dict() for c in self.children]
        }