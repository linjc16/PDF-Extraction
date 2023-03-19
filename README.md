# Pipeline for Table and Figure Extraction from Papers
## Quick Start
First, use [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) to extract text, tables and figures from each paper.
```
bash scripts/1_paddle.sh
```
Then, use the results from the last step to output the final extracted samples.
```
bash scripts/2_match.sh
```

## Table/Figure Extraction
### PDF to Images
Since PDF is non-structure file format, it is hard to extract components in PDF precisely. To remedy this issue, we consider using OCR techniques. We first convert PDF to images page by page by using [PyMuPDF](https://github.com/pymupdf/PyMuPDF). To improve the performance of the following OCR operation, these images are unpsamped 8x to get high resolution inputs. 

### Extraction of Text, Tables and Figures
We then use [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) to extract text, tables and figures. The format of the output is a `dict`:
```
{
    "type": ,
    "bbox": ,
    "res":[
        {
            "text":
            "confidence":
            "text_region":
        },
        {
            ...
        }
    ]
    "img_idx": 
}
```
where `type` contains text, figures, tables and so forth. `bbox` is the bounding box coordinates. `res` is the extraction results and is a `List` contains several `dict`. `img_idx` means the page id.

For tables, we save the the `html`, `*.png` and `*.xlsx` files. For figures, we save `*.png` files.

### OCR Text Refinement
The output of the [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) is not always accurate. For example, it sometimes miss the first few letters of a paragraph. Therefore, we use the original PDF text to refine the OCR output. More specifically, we first use [PyMuPDF](https://github.com/pymupdf/PyMuPDF) to read the text in PDF files. Then, for each page, we use `Fuzzy Matching Algorithm` to align each OCR text (line by line) with corresponding pdf text. Finally, we obtained refined OCR text.

### Caption Matching
Next, for the convenience of the mathching operation between passages and figures/tables, we should extract the id and caption of each figure/table. For this part, we implement a `Topk Nearest Bounding Box Algorithm` to extract the captions and then use regular expression to get the id. Concretely, from the output of [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR), we get bounding box of text and figures/tables. Then, for each figure/table, we try to extract its id from its topK nearest text blocks by regular expression. If obtain the id, then the text of the id is viewed as the caption.

### Passage Matching
Now that we have extract the ids of figures/tables, we then can find all the passages which are related to the figures/tables. For each passage in the refined OCR text, we find if there exist any Figure/Table id. If so, this passage is aligned with that figure/table.

### Data Format
For each paper, we save the sample as the following dict:
```
{
    'src': ,
    'paper_id': ,
    'pdf_path': ,
    'table': [
        {
            'excel_path': ,
            'fig_path': ,
            'id': ,
            'caption': ,
            'ocr_caption': ,
            'html': ,
            'bbox':, 
            'img_idx': ,
            'passage': 
        },
        {

        }, ...
    ]
    'figure': [
        {
            'fig_path': ,
            'id': ,
            'caption': ,
            'ocr_caption': ,
            'bbox': ,
            'img_idx': ,
            'passage'
        },
        {

        }, ...
    ]
}
```

### Limitations
Currently, there are still some limitations for this pipeline despite its great performance:
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) may miss some passages. If these passages are captions, the id of related figures/tables will not be extracted. Therefore, we just saved these samples with a `None` id.
- PaddleOCR may fail to detect some hard tables and fail to extract them. 
- PaddleOCR may not detect some short text lines, such as very short captions.
- PaadleOCR may detect some plain passages as figures/tables, such as references or Algorihtm blocks.

