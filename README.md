<div align="center">    
 
# Integrating Temporal Attention into Dynamic Multi-Contrast MRI Reconstruction

</div>

This project repository contains the PyTorch implementation of our unrolled model for multi-contrast Cardiac MRI reconstruction

**Contact**
- Nicolas Carpenter: ngcarpen@ualberta.ca


## Method
TODO
  
![Contrasts Image](projet/support/Task1&2_ContrastImageCMR.png "Contrasts and Views")

![Masks Image](projet/support/Task1&2_MaskCMR.png "Undersampling Masks")


## How to install
```bash
# clone project   
git clone https://github.com/NicoCarpe/CMRxRecon.git
 ```

## Project Structure
Our directory structure looks similar to this:

```
├── configs                        <- Training, evaluation, and environment configs
├── datasets                    
├── imgs                        
├── output                         <- Experiment log and checkpoints will be saved here once you train a model
├── pretrained_models              <- Pretrained model checkpoints
├── project                 
│   ├── data_modules           
│   │    ├── data_module.py        <- PyTorch Lightning module for data 
│   │    └── model_module.py       <- PyTorch Lightning module for model
│   │
│   ├── data_utils               
│   │    ├── basemodel.py          <- Provides methods for building, saving, and loading model states
│   │    ├── CNN.py                <- UNet implementation
│   │    ├── fS2RT3D.py            <- Sensitivity map refinement and dual-domain reconstruction block
│   │    ├── metrics.py            <- Metrics for model evaluation
│   │    ├── model.py              <- Unrolled reconstruction model
│   │    ├── sensitivity_model.py  <- Sensitivity map estimation 
│   │    └── SwinTransformer3D.py  <- 3d image domain swin transformer
│   │
│   ├── eval                       <- Code for model evaluation
│   ├── model                   
│   │    ├── mri_datasets.py       <- Dataset Class for each dataset
│   │    ├── transforms.py         <- Dataset Class for each dataset
│   │    └── preprocessing.py      <-
│   │
│   ├── support                    <- Supporting code for CMRxRecon2024 challenge
│   └── training                   <- Code for model training
│ 
├── scripts                        <- Bash scripts for training and evaluation
├── .gitignore                     <- List of files/folders ignored by git
└── README.md
```

<br>

## Training/Inference

Scripts are provided to run this model using SLURM. After adjusting the train_config.yaml file, submit_batch_train.sh can be used to schedule the data preprocessing and the training of the model.

After adjusting the eval_config.yaml file, submit_batch_eval.sh can be used to schedule the testing of the specified model checkpoint.

## Citation
```bibtex

}
```

## Acknowledgements
TODO

