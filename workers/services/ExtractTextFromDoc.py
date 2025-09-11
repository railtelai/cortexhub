import base64
import fitz
from typing import Any, List, Tuple, Optional, cast
import pandas as pd
import os


from workers.implementations import ExtractTextFromDocImpl


class ExtractTextFromDoc(ExtractTextFromDocImpl):

    def ExtractTextFromXlsx(self, docPath: str) -> str:
        xls = pd.ExcelFile(docPath)
        allText: list[str] = []

        for sheetName in xls.sheet_names:
            df = cast(Any, pd).read_excel(docPath, sheet_name=sheetName, header=None)

            for row in df.itertuples(index=False):
                rowText = "  ".join(
                    "" if cast(Any, pd).isna(cell) else str(cell) for cell in row
                )
                if rowText.strip():
                    allText.append(rowText)

        return "\n".join(allText)

    def ExtractTextFromCsv(self, docPath: str) -> str:
        df = cast(Any, pd).read_csv(docPath, header=None)
        allText: list[str] = []

        for row in df.itertuples(index=False):
            for col_index, value in enumerate(row):
                if cast(Any, pd).isna(value):
                    value = None
                else:
                    text = str(value).strip()
                    value = text if text else "None"
                allText.append(f"<<C{col_index+1}-START>>{value}<<C{col_index+1}-END>>")

        return "\n".join(allText)

    def ExtractTextAndImagesFromPdf(self, docPath: str) -> Tuple[str, List[str]]:
        doc: Any = fitz.open(docPath)
        imagesB64: List[str] = []
        imageCounter: int = 1
        finalTextParts: List[str] = []

        for _, page in enumerate(doc, start=1):
            blocks = page.get_text("dict")["blocks"]
            pageItems: List[Tuple[str, float, str]] = []

            for block in blocks:
                if block["type"] == 0:  # text block
                    for line in block.get("lines", []):
                        y0 = line["bbox"][1]
                        lineText = " ".join(
                            span.get("text", "")
                            for span in line.get("spans", [])
                            if "text" in span
                        ).strip()
                        if lineText:
                            pageItems.append(("text", y0, lineText))
                elif block["type"] == 1:  # image block
                    y0 = block["bbox"][1]
                    imgId = f"image-{imageCounter}"
                    placeholder = f"<<{imgId}>>"

                    xref: Optional[int] = block.get("image") or block.get("number")
                    baseImage = None
                    if isinstance(xref, int) and xref > 0:
                        try:
                            baseImage = doc.extract_image(xref)
                        except Exception:
                            baseImage = None

                    if baseImage and baseImage.get("image"):
                        data = baseImage["image"]
                    else:
                        try:
                            rect = fitz.Rect(block["bbox"])
                            pix = page.get_pixmap(
                                matrix=fitz.Matrix(2, 2), clip=rect, alpha=False
                            )
                            data = pix.tobytes("png")
                        except Exception:
                            data = b""

                    b64Str = base64.b64encode(data).decode("utf-8") if data else ""
                    imagesB64.append(b64Str)
                    pageItems.append(("image", y0, placeholder))
                    imageCounter += 1

            pageItems.sort(key=lambda x: x[1])
            for itemType, _, content in pageItems:
                if itemType == "text":
                    finalTextParts.append(content)
                else:
                    finalTextParts.append(f"\n{content}\n")

        return "\n".join(finalTextParts), imagesB64

    def ExtractTextFromDoc(self, docPath: str) -> Tuple[str, List[str]]:
        ext = os.path.splitext(docPath)[1].lower()
        if ext == ".pdf":
            return self.ExtractTextAndImagesFromPdf(docPath)
        elif ext in [".xlsx", ".xls"]:
            return self.ExtractTextFromXlsx(docPath), []
        elif ext == ".csv":
            return self.ExtractTextFromCsv(docPath), []
        else:
            raise ValueError(f"Unsupported file format: {ext}")
