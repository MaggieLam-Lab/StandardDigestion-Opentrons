# Opentrons Shotgun Proteomics Sample Preparation Protocol v.0.1.1

This repository houses the scripts to be used in the protocol to automate  experimental steps in proteomics sample preparation with the Opentrons OT-2 automated liquid handling systems.

Three digestion scripts are provided in the `digestion_scripts` folder:

- `NoSP3_digestion.py`: Digestion without SP3 detergent removal
- `SP3_digestion.py`: Digestion with SP3 detergent removal
- `SP3_peptide_cleanup.py`: Post-digestion SP3 peptide cleanup

In addition, one helper script is provided in the `misc_scripts` folder:

- `BCA_protocol.py`: Total protein quantification using BCA assay


## Getting Started


#### Hardware requirements

This protocol requires an Opentrons OT-2 automated liquid handling system along with suitable accessories:

- OT-2 pipettes
- Pipette tips
- 4-in-1 tube rack set
- Aluminum block set
- Magnetic module
- Temperature module
- 96-well 2mL deep well plates

#### Software requirements

- Python v.3.5+
- Opentrons API v2

The Opentrons API v2 can be acquired in `pip` via:

```
pip install opentrons
```



Digestion scripts created and developed by Erin Yu Han, Cody Thomas, and Sara Wennersten. 


## Authors

* **Erin Yu Han, PhD** - *Code/design* - [EYH](https://github.com/ErinYH)
* **Cody Thomas, BSc** - *Code/design* - [CodyT21](https://github.com/CodyT21)
* **Sara Wennersten, BSc** - *Code/design* - [sara-wennersten](https://github.com/sara-wennersten)

## Additional Information

See also the [Opentrons API v2 documentation]https://docs.opentrons.com/v2/).

## Contributing

Please contact us if you wish to contribute, and submit pull requests to us.


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.