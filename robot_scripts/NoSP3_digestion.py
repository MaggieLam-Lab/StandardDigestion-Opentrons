from opentrons import protocol_api
import datetime

metadata = {
    'protocolName': 'Digestion Protocol 2mL Tubes',
    'author': 'Cody',
    'description': 'Digestion protocol for use with 2mL tubes',
    'apiLevel': '2.8'
}


def run(protocol: protocol_api.ProtocolContext):
    # ---------------------------- CUSTOMIZE HERE ONLY ---------------------------- |
    number_of_samples: int = 1  # Total number of samples (including replicates) cannot exceed 24
    # Length of sample_concentrations list must match the number of the samples above.
    sample_concentrations = [2.0]  # Compatible protein sample concentration range: >0.75 ug/uL -- CHANGE IN THE FUTURE
    replicates: int = 9
    volume_of_DTT: float = 10.0  # manually prepare 60mM DTT in MS-grade water
    volume_of_IAA: float = 10.0  # manually prepare 375mM IAA in MS-grade water
    volume_of_trypsin: float = 10.0  # manually prepare to a concentration of 0.2ug/uL
    incubation_time_DTT = 30  # in minutes
    incubation_time_IAA = 30  # in minutes
    starting_tip_p50 = 'C1'  # change if full tip rack will not be used
    starting_tip_p300 = 'A1'  # change if full tip rack will not be used

    # | ---------------------------- ^^^^^^^^^^^^^^^^^^^ ---------------------------- |
    # ---------------------------- DO NOT EDIT BELOW THIS LINE ---------------------------- #
    # Check for valid inputs
    if len(sample_concentrations) != number_of_samples:
        raise ValueError('Length of sample_concentrations must match the integer specified for number_of_samples.')
    if number_of_samples * replicates > 24:
        raise ValueError('Total digests (including replicates) cannot exceed the number of slots available on the aluminum block (24).')
    if any(sample_concentrations) < 1:  # CHANGE IN THE FUTURE
        raise ValueError('Sample concentrations must be greater than 1 ug/uL.')  # CHANGE CONCENTRATION IN ERROR

    # | ---------  tip racks --------- |
    tiprack_300 = protocol.load_labware('opentrons_96_tiprack_300ul', 2)
    tiprack_50 = protocol.load_labware('opentrons_96_tiprack_300ul', 1)

    # | ---------  pipettes --------- |
    p300 = protocol.load_instrument('p300_single', 'right', tip_racks=[tiprack_300])
    p50 = protocol.load_instrument('p50_single', 'left', tip_racks=[tiprack_50])
    p50.starting_tip = tiprack_50.well(starting_tip_p50)
    p300.starting_tip = tiprack_300.well(starting_tip_p300)

    # | ---------  tube racks/plates/containers --------- |
    temp_mod = protocol.load_module('Temperature Module', 10)
    temp_plate = temp_mod.load_labware('opentrons_24_aluminumblock_nest_2ml_snapcap')
    tuberack_2mL = protocol.load_labware('opentrons_24_tuberack_nest_2ml_snapcap', 4)
    tuberack_15ml_50ml = protocol.load_labware('opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical', 5)

    # | --------- reagents --------- |
    DTT = tuberack_2mL['A6']
    IAA = tuberack_2mL['B6']
    trypsin = tuberack_2mL['C6']
    ABC = tuberack_15ml_50ml['A3']
    samples = tuberack_2mL.wells()[:number_of_samples]

    # ---------------------------- COMMANDS ---------------------------- #

    # | --------- transfer samples to plate --------- |
    protocol.pause('Ensure to change starting tip position for p50 and p300.')

    for i in range(number_of_samples):
        # If sample concentration is greater than 1 ug/uL, transfer ABC then 100ug of sample to well plate for
        # 100uL of 1 ug/uL sample. P300 is used to transfer ABC if ABC transfer volume is greater than 50uL.
                  # transfer ABC
            if (100 - (100 / sample_concentrations[i])) > 50:
                p300.transfer(
                    100 - (100 / sample_concentrations[i]),
                    ABC,
                    temp_plate.wells()[i * replicates: i * replicates + replicates],
                    new_tip='once',
                    touch_tip=True
                )
            else:
                p50.transfer(
                    100 - (100 / sample_concentrations[i]),
                    ABC,
                    temp_plate.wells()[i * replicates: i * replicates + replicates],
                    new_tip='once',
                    touch_tip=True
                )

    #       transfer 100ug of protein and mix 3 times with 50 uL volume
            if (100 / sample_concentrations[i]) > 50:
                p300.transfer(
                100 / sample_concentrations[i],
                samples[i],
                temp_plate.wells()[i * replicates: i * replicates + replicates],
                mix_after=(3, 50),
                new_tip='always',
                touch_tip=True,
                blow_out=True,
                blowout_location='destination well'
                )
            else:
                p50.transfer(
                100 / sample_concentrations[i],
                samples[i],
                temp_plate.wells()[i * replicates: i * replicates + replicates],
                mix_after=(3, 50),
                new_tip='always',
                touch_tip=True,
                blow_out=True,
                blowout_location='destination well'
            )



    # | --------- transfer DTT to plate --------- |
    protocol.pause('Ensure DTT has been loaded into A6 of the 2ml tube rack located in slot 4 prior to resuming protocol.')
    p50.transfer(
        volume_of_DTT,
        DTT,
        temp_plate.wells()[:number_of_samples * replicates],
        mix_after=(5, 50),
        new_tip='always',
        touch_tip=True,
        blow_out=True,
        blowout_location='destination well'
    )
    protocol.pause('Ensure to close tube caps.')

    # | --------- first incubation --------- |
    temp_mod.set_temperature(55)
    protocol.delay(minutes=5, msg='Pausing for 5 minutes to allow samples to reach tempeature.')
    protocol.delay(minutes=incubation_time_DTT, msg=f'Incubating at 55 degrees for {incubation_time_DTT} minutes.')

    # | --------- set block to room temp before adding IAA --------- |
    protocol.comment('Cooling down temp block.')
    temp_mod.set_temperature(22)
    protocol.delay(minutes=5, msg='Pausing for 5 minutes to allow tubes to cool down.')
    protocol.pause('Ensure to open tube caps.')

    # | --------- transfer IAA to samples on plate --------- |
    protocol.pause('Ensure IAA has been loaded into B6 of the 2ml tube rack located in slot 4 prior to resuming protocol.')
    p50.transfer(
        volume_of_IAA,
        IAA,
        temp_plate.wells()[:number_of_samples * replicates],
        mix_after=(5, 50),
        new_tip='always',
        touch_tip=True,
        blow_out=True,
        blowout_location='destination well'
    )
    protocol.pause('Close caps and cover tubes with foil')

    # | --------- second incubation --------- |
    temp_mod.set_temperature(22)
    protocol.delay(minutes=incubation_time_IAA, msg=f'Protect tubes from light. Incubating at 22 degrees for {incubation_time_IAA} minutes.')
    protocol.comment('Temp block will now be deactivated.')
    temp_mod.deactivate()
 

    # | --------- transfer trypsin to samples on plate --------- |
    protocol.pause('Ensure trypsin has been loaded into C6 of the 2ml tube rack located in slot 4 prior to resuming protocol.')
    protocol.pause('Open tube caps')
    p50.transfer(
        volume_of_trypsin,
        trypsin,
        temp_plate.wells()[:number_of_samples * replicates],
        mix_after=(5, 50),
        new_tip='always',
        touch_tip=True,
        blow_out=True,
        blowout_location='destination well')
    protocol.comment('Transfer to tubes to shaker for overnight digestion.')
