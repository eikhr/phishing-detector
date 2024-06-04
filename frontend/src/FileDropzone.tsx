import { Button, DropZone, FileTrigger, Text } from "react-aria-components";
import type { FileDropItem } from "react-aria";
import "./FileDropzone.css";

const FileDropzone = ({
  setFile,
}: {
  setFile: (file: File | FileDropItem) => void;
}) => {
  return (
    <DropZone
      onDrop={(e) => {
        const files = e.items.filter(
          (file) => file.kind === "file",
        ) as FileDropItem[];
        setFile(files[0]);
      }}
    >
      <FileTrigger
        acceptedFileTypes={[".txt", ".eml"]}
        onSelect={(e) => {
          const files = Array.from(e ?? []);
          setFile(files[0]);
        }}
      >
        <Button>Select files</Button>
      </FileTrigger>
      <Text slot="label" style={{ display: "block" }}>
        {"Drop an .eml file here"}
      </Text>
    </DropZone>
  );
};

export default FileDropzone;
