from os import path, sep, walk
from json import dump
import argparse
from model.filesystementity import FilesystemEntity

def main():
    parser = argparse.ArgumentParser(prog="SystemStorageAnalyzer", description="This program collects and reports information on storage consumed on disk.")
    parser.add_argument('-p', '--path', required=True)
    parser.add_argument('--json', required=False)
    parser.add_argument('--csv', required=False)

    args = parser.parse_args()
    base_dir = args.path
    dir_walker = walk(base_dir)

    directories_map = {}
    root_entity = None

    while dir_content := next(dir_walker, None):
        # Identify where we are in the file system
        current_dir = dir_content[0]
        parent_path = sep.join(current_dir.split(sep)[:-1])

        # Create a FilesystemEntity for this directory
        dir_entity = FilesystemEntity(full_path=current_dir, created_at=path.getctime(current_dir))
        directories_map.update({current_dir: dir_entity})
        if not root_entity:
            root_entity = dir_entity

        # Associate this entity with its parent if one exists
        parent_entity = directories_map.get(parent_path, None)
        if parent_entity is not None:
            parent_entity.add_child(dir_entity)

        # Handle child files of this directory
        child_files = dir_content[2]
        for file_name in child_files:
            child_path = sep.join([current_dir, file_name])
            child_entity = FilesystemEntity(child_path, created_at=path.getctime(child_path))
            dir_entity.add_child(child_entity)

    # Handle JSON output if requested
    if root_entity is not None and args.json:
        with open(args.json, "w", encoding="utf-8") as outfile:
            dump(root_entity.to_dict(), outfile, indent=4)

    # Handle CSV output if requested
    # * For now, use super simple approach so we don't need external dependencies
    if root_entity is not None and args.csv:
        with open(args.csv, "w", encoding="utf-8") as outfile:
            header_line ="Name,Is Directory,Size,Rounded Size,Created,Last Modified,Children,Depth,Full Path\n"
            all_children = root_entity.get_all_children_flattened()
            all_entities = [root_entity] + all_children
            lines = [header_line]
            for entity in all_entities:
                entity_attribs = [
                    entity.get_name(), str(entity.is_dir()), str(entity.get_size()), entity.get_size_rounded(),
                    entity.get_created_timestamp(), entity.get_modified_timestamp(), str(len(entity.children)),
                    str(entity.depth), entity.full_path
                ]
                # * Note: Despite File I/O slugishness, might be more memory efficient to write one line at a time. Need to test.
                lines.append(",".join(entity_attribs)+"\n")
            outfile.writelines(lines)


if __name__ == "__main__":
    main()