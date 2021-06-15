from opentrons import protocol_api

metadata = {
    'protocolName': 'BCA Protocol Practice',
    'author': 'Cody',
    'description': 'Recreating BCA script from github',
    'apiLevel': '2.8'
}


def run(protocol: protocol_api.ProtocolContext):

    # | --------- Customize --------- |
    num_samples = 3  # If dilution is required, dilute the samples prior to loading on the robot
    num_standards = 9
    volume_standard: float = 25.0
    volume_sample: float = 25.0
    volume_WR: float = 200
    replicates_standards = 3
    replicates_samples = 3
    total_samples = num_standards * replicates_standards + num_samples * replicates_samples
    starting_tip_p50 = 'E2'  # change if full tip rack will not be used
    starting_tip_p300 = 'B1'  # change if full tip rack will not be used

    # | --------- Tip Racks --------- |
    tiprack_50 = protocol.load_labware('opentrons_96_tiprack_300ul', 1)
    tiprack_300 = protocol.load_labware('opentrons_96_tiprack_300ul', 2)

    # | --------- Pipettes --------- |
    p50 = protocol.load_instrument('p50_single', 'left', tip_racks=[tiprack_50])
    p300 = protocol.load_instrument('p300_single', 'right', tip_racks=[tiprack_300])
    p50.starting_tip = tiprack_50.well(starting_tip_p50)
    p300.starting_tip = tiprack_300.well(starting_tip_p300)

    # | --------- Tube Racks/Plates/Containers --------- |
    plate_96_well = protocol.load_labware('nest_96_wellplate_200ul_flat', 3)
    tuberack_2ml = protocol.load_labware('opentrons_24_tuberack_nest_2ml_snapcap', 4)
    tuberack_15ml_50ml = protocol.load_labware('opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical', 5)

    # | --------- Reagents --------- |
    WR_15 = tuberack_15ml_50ml['A1']
    WR_50 = tuberack_15ml_50ml['A3']
    # if more than 15mL of working reagent is needed, use WR_50 located in A3. Change code on line 46 to WR_50.

    #transfer standards to well plate
    for std in range(num_standards):
        p50.distribute(
            volume_standard,
            tuberack_2ml.wells()[std],
            plate_96_well.wells()[(std * replicates_standards) :
                                  (std * replicates_standards) + replicates_standards],
            touch_tip=True,
            new_tip='once',
            blow_out=True,
            blowout_location='source well'
        )

    # transfer samples to plate
    for sample in range(num_samples):
        p50.distribute(
            volume_sample,
            tuberack_2ml.wells()[sample + num_standards], #this tells where to pick up the sample in 2.0mL tube rack
            plate_96_well.wells()[(sample * replicates_samples) + (num_standards * replicates_standards):
                                  (sample * replicates_samples) + (num_standards * replicates_standards) + replicates_samples],
            touch_tip=True,
            new_tip='once',
            blow_out=True,
            blowout_location='source well'
        )

    # transfer working reagent to the well plate
    p300.pick_up_tip()
    for well in plate_96_well.wells()[:total_samples]:
       p300.transfer(
           volume_WR,
           WR_50,
           well.top(),
           blow_out = True,
           blowout_location = 'destination well',
           new_tip='never',
        )
    p300.drop_tip()
    protocol.comment('Incubate plate at 37C for 30 minutes prior to measuring absorbance at 562nm.')
