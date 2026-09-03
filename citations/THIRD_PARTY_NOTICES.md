# Third party data, software, and citation notices

This repository separates the project software license from the terms that
apply to datasets, source images, third party tools, and model weights. It does
not redistribute CT volumes, DICOM files, training labels, or patient linked
manifests.

The [MIT license](LICENSE) applies to the project software and documentation
and preserves the University Medicine Essen notice for retained SAROS code. It
does not relicense any dataset, source image collection, third party software,
or model checkpoint.

## SAROS and TCIA

Agent 1 was developed from the SAROS body region workflow. Local provenance
records use the September 2023 SAROS information spreadsheet and therefore
identify the training source as SAROS Version 1.

- SAROS source code: University Medicine Essen, MIT License,
  <https://github.com/UMEssen/saros-dataset>.
- SAROS data page: <https://www.cancerimagingarchive.net/analysis-result/saros/>.
- SAROS Version 1 segmentations and information spreadsheet: CC BY 4.0.
- SAROS CT images: obtained from 28 TCIA collections. The originating
  collection retains its own access and license terms, which include CC BY
  3.0, CC BY-NC 3.0, CC BY 4.0, and controlled access terms.
- TCIA policy: <https://www.cancerimagingarchive.net/data-usage-policies-and-restrictions/>.

The recorded Agent 1 training split used 750 SAROS cases. Of these, 144 came
from six collections now identified by TCIA as controlled access:
ACRIN-HNSCC-FDG-PET/CT, Anti-PD-1_MELANOMA, HNSCC, Head-Neck Cetuximab,
QIN-HEADNECK, and TCGA-HNSC. TCIA's Restricted License permits publication of
project results but limits use and redistribution of the dataset and certain
derivatives. The project records do not contain written confirmation that a
public checkpoint falls within the approved publication scope. The Agent 1
checkpoint is therefore withheld from this release pending confirmation from
the applicable agreement holder or TCIA/UAMS.

Required SAROS data citation:

Koitka, S., Baldini, G., Kroll, L., van Landeghem, N., Haubold, J., Sung Kim,
M., Kleesiek, J., Nensa, F., & Hosch, R. (2023). *SAROS – A large,
heterogeneous, and sparsely annotated segmentation dataset on CT imaging data
(SAROS) (Version 1).* The Cancer Imaging Archive.
<https://doi.org/10.25737/SZ96-ZG60>

Recommended SAROS publication:

Koitka, S., Baldini, G., Kroll, L., van Landeghem, N., Pollok, O. B., Haubold,
J., Pelka, O., Kim, M., Kleesiek, J., Nensa, F., & Hosch, R. (2024). *SAROS: A
dataset for whole-body region and organ segmentation in CT imaging.* Scientific
Data, 11. <https://doi.org/10.1038/s41597-024-03337-6>

TCIA citation:

Clark, K., Vendt, B., Smith, K., Freymann, J., Kirby, J., Koppel, P., Moore,
S., Phillips, S., Maffitt, D., Pringle, M., Tarbox, L., & Prior, F. (2013).
*The Cancer Imaging Archive: Maintaining and Operating a Public Information
Repository.* Journal of Digital Imaging, 26(6), 1045–1057.
<https://doi.org/10.1007/s10278-013-9622-7>

## TotalSegmentator

Agent 2 pretraining used 947 CT volumes selected from Version 2.0.1 of the
1,228 case TotalSegmentator dataset. The training manifests contain 805 cases
for training and 142 for validation. Pseudolabels were generated from the
`pericardium` output of the `trunk_cavities` task, followed by removal of 10%
of the positive axial support at each end.

- TotalSegmentator CT dataset Version 2.0.1: CC BY 4.0,
  <https://doi.org/10.5281/zenodo.10047292>.
- TotalSegmentator software and the `trunk_cavities` task: Apache License 2.0.
  The audited baseline is documented in the
  [Version 2.18.0 README](https://github.com/wasserth/TotalSegmentator/blob/v2.18.0/README.md)
  and [license](https://github.com/wasserth/TotalSegmentator/blob/v2.18.0/LICENSE).
- The generation log records the task and trimming rule but not the installed
  TotalSegmentator package version. Version 2.18.0 was present when this
  repository was audited on 2026-09-03; it is a reproduction baseline, not a
  claim about the unrecorded historical run version.

TotalSegmentator dataset citation:

Wasserthal, J. (2023). *Dataset with segmentations of 117 important anatomical
structures in 1228 CT images* (Version 2.0.1). Zenodo.
<https://doi.org/10.5281/zenodo.10047292>

TotalSegmentator software citation:

Wasserthal, J., Breit, H.-C., Meyer, M. T., Pradella, M., Hinck, D., Sauter,
A. W., Heye, T., Boll, D., Cyriac, J., Yang, S., Bach, M., & Segeroth, M.
(2023). *TotalSegmentator: Robust Segmentation of 104 Anatomic Structures in CT
Images.* Radiology: Artificial Intelligence, 5.
<https://doi.org/10.1148/ryai.230024>

TotalSegmentator also requests citation of nnU Net:

Isensee, F., Jaeger, P. F., Kohl, S. A. A., Petersen, J., & Maier-Hein, K. H.
(2021). *nnU-Net: a self-configuring method for deep learning based biomedical
image segmentation.* Nature Methods, 18, 203–211.
<https://doi.org/10.1038/s41592-020-01008-z>

## Visual Lab Cardiac Fat Database

Agent 2 refinement and held out evaluation used all 20 noncontrast cardiac CT
cases from the Visual Lab Cardiac Fat Database (CT-FAT), Universidade Federal
Fluminense. Nineteen cases were used for refinement and the twentieth was kept
outside training and checkpoint selection for the reported held out test. The
source page permits use of its ground truth when the published work is cited.
The source DICOM files and manual ground truth are not redistributed here.

- Dataset page: <https://visual.ic.uff.br/en/cardio/ctfat/>.
- Required citation:

Rodrigues, E. O., Morais, F. F. C., Morais, N. A. O. S., Conci, L. S., Neto,
L. V., & Conci, A. (2016). *A novel approach for the automated segmentation
and volume quantification of cardiac fats on computed tomography.* Computer
Methods and Programs in Biomedicine, 123, 109-128.
<https://doi.org/10.1016/j.cmpb.2015.09.017>

## Demo CT: NSCLC Radiomics

The inference recording uses public NSCLC Radiomics Version 4 CT case
`LUNG1-319` from The Cancer Imaging Archive. The source series UID is
`1.3.6.1.4.1.32722.99.99.257803739023845165540111357191929268253`.
The collection is licensed under CC BY-NC 3.0:
<https://creativecommons.org/licenses/by-nc/3.0/>.
Collection page:
<https://www.cancerimagingarchive.net/collection/nsclc-radiomics/>.

The source DICOM series was converted to NIfTI and renamed
`case_002_0000.nii.gz` for local inference. The original and viewer-input
NIfTI copies have SHA-256
`b1cb92cd74f81865e796ce95a61191e48eb0f9345590af7a20ef4b55f587f1e0`.
The published recording adds model overlays and viewer controls, shortens the
inference wait, and accelerates part of the result review. The CT volume and
source DICOM files are not included in this repository. Because the recordings
reproduce this CT, both demo video files are distributed under CC BY-NC 3.0.

Required NSCLC Radiomics data citation:

Aerts, H. J. W. L., Wee, L., Rios Velazquez, E., Leijenaar, R. T. H., Parmar,
C., Grossmann, P., Carvalho, S., Bussink, J., Monshouwer, R., Haibe-Kains, B.,
Rietveld, D., Hoebers, F., Rietbergen, M. M., Leemans, C. R., Dekker, A.,
Quackenbush, J., Gillies, R. J., & Lambin, P. (2014). *Data From NSCLC
Radiomics (Version 4).* The Cancer Imaging Archive.
<https://doi.org/10.7937/K9/TCIA.2015.PF0M9REI>

Recommended NSCLC Radiomics publication:

Aerts, H. J. W. L., Velazquez, E. R., Leijenaar, R. T. H., Parmar, C.,
Grossmann, P., Carvalho, S., Bussink, J., Monshouwer, R., Haibe-Kains, B.,
Rietveld, D., Hoebers, F., Rietbergen, M. M., Leemans, C. R., Dekker, A.,
Quackenbush, J., Gillies, R. J., & Lambin, P. (2014). *Decoding tumour
phenotype by noninvasive imaging using a quantitative radiomics approach.*
Nature Communications, 5. <https://doi.org/10.1038/ncomms5006>

## Model weight distribution

The GitHub Release checkpoint is a separate artifact from the MIT licensed
software. Agent 2 learned from TotalSegmentator CTs and derived pseudolabels,
then from 19 CT-FAT cases with manual ground truth. Training data and labels
are not redistributed.

The project owner authorized distribution of the frozen Agent 2 checkpoint on
September 3, 2026. It is licensed under CC BY-NC 4.0 as described in
[`MODEL_WEIGHTS_LICENSE.md`](MODEL_WEIGHTS_LICENSE.md). This licensing decision
does not alter or replace any source dataset, image collection, annotation, or
third party software terms. The release archive includes this notice, the
model weight license, and the Agent 2 model card. The Agent 1 checkpoint is
withheld for the controlled access reason documented above.
