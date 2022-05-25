# Grammar-analysis: Linguistic Features Extraction from Reference Grammars

> This repository contains materials for the [coursework](/grammar-analysis_Kozlova.pdf) “Linguistic Features Extraction from Reference Grammars”.

The goal of this paper is to create a online-resource for automatic recognition and analysis of morphological features, extracted from structured linguistic data[^1] in grammar books. </br>
Unfortunately, the provided website do not have a permanent link yet, so now it is possible only to run the code on your computer and generate a temporary link.

[^1]: such as morphological tables and glossed examples 

## Installation
1. There are two files in repository: [`.py`](/grammar-analysis.py) is created for Jupiter Notebook and [`.ipynb`](/grammar_analysis.ipynd) is set up for Google Colab.
2. In Jupiter Notebook these libraries: __pdfplumber__, __gdown__, - are required. If not installed, run:
``` python
!pip install pdfplumber
!pip install gdown
```
3. In Google Colab code includes cells that upload required packages. <br>
However, after installation there is one difficulty in Colab. You will have to find `/etc/ImageMagick-6/policy.xml` file and change one string there: `<policy domain="coder" rights="none" pattern="PDF"/>` → `<policy domain="coder" rights="read|write" pattern="PDF"/>`.<br>
Or you can delete `/etc/ImageMagick-6/policy.xml` file and upload [this one](/policy.xml) at it's place.<br>
Do not forget to *Restart runtime* after this procedure.
4. Create folder `/static` in the same directory. 

## Data
### Input
Using this site, you can upload your grammar in `.pdf` format (check out the [requirements](#requirements) first) or choose one from a drop-down list ([table](https://docs.google.com/spreadsheets/d/1fbmrfa_qDXIOfdwD8Z33YKBQpJ0VL9P0A31x3VjnF8k/) with avaliable grammars).<br>
<br>
#### Uploading instruction:
![uploading](/static/site_1.png)
<br>
#### Choosing instruction:
![choosing](/static/site_2.png)

### Output
1. a table with “morpheme-gloss” pairs and a full list of examples/tables, where this pair occur:

|    ID |    Gloss |    Affix |    Examples                                                                         |
|-----------|--------------|--------------|-----------------------------------------------------------------------------------------|
|    20 |    1SG   |    -nu-  |    p. 518 (18), p. 554 (119),   p. 555 (121), p. 388 tab. (8.17), p. 414 tab. (9.4) |

2. a table with IMG[^2] and numbers of page and example

| ID           | Number Example | Page | Example                                 | Glossing                                                               | Translation                            |
|--------------|----------------|------|-----------------------------------------|------------------------------------------------------------------------|----------------------------------------|
| 51           | 18             | 518  | ʃiiha anɨ‑a‑ha‑i wɨ‑tasa‑nu‑ʃa ta‑wa‑ka | very desire‑IMPFV‑1SG‑DECL go:PFV‑INTENT‑1SG‑UNCERT say+IMPFV‑3‑POLINT | ‘is she saying “I really want to go”?’ |

3. a folder with cropped (left) and recognized (right) morphological tables:

<img align='left' src='/static/example.jpeg' alt='385_8. 15: First and second person markers on past declarative verbs' width='420'>

| PERSON | SINGULAR | NON-SINGULAR |
|--------|----------|--------------|
| 1      | -ha      | -hi          |
| 2      | -umɨ     | -uhumɨ       |

#### Downloading instruction:
At the botton of the `/results` page of the site you can find a drop-down with options to download:

![downloading](/static/site_3.png)
<br>
Choose one option and press `Submit` button.<br>
Selected files will be downloaded to your computer. 


### Requirements:
#### *Grammars*
:white_check_mark: machine-readable PDF</br>
:question: scanned and digitized)
#### *Glosses*
:white_check_mark: explicit numeration</br>
:white_check_mark: IMG[^2] and LGR[^3] usage</br>
:white_check_mark: explicit markers of translation (apostrophes or quotes)</br>
:question: first line(s) to omit</br>
:question: text wrapping to the next line
#### *Tables*
:white_check_mark: explicit table borders

[^2]: Interlinear Morphemic Glossing
[^3]: Leipzig Glossing Rules

## Contacts:
*Kate Kozlova*<br>
:telephone_receiver: [telegram](https://t.me/da_budet_tak)<br>
:computer:[e-mail](mailto:erkozlova_2@edu.hse.ru)
