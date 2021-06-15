from opentrons import protocol_api


metadata = {
    'protocolName': 'SP3 Protein Cleanup and Digestion',
    'author': 'Cody',
    'description': 'Digestion protocol with SP3 detergent removal',
    'apiLevel': '2.8'
}


def run(protocol: protocol_api.ProtocolContext):
    # ---------------------------- CUSTOMIZE HERE ONLY ---------------------------- |
    number_of_samples: int = 1
    # Length of sample_concentrations list must match the number of the samples above.
    sample_concentrations = [5.00]  # Compatible protein sample concentration range: >2.0 ug/uL
    replicates: int = 3
    volume_of_DTT: float = 10.0  # manually prepare 60mM DTT in MS-grade water
    volume_of_IAA: float = 10.0  # manually prepare 375mM IAA in MS-grade water
    volume_of_trypsin: float = 10.0  # manually prepare to a concentration of 0.2ug/uL
    incubation_time_DTT = 30  # in minutes
    incubation_time_IAA = 30  # in minutes
    volume_of_beads: float = 20.0  # Manually prepare beads for peptide binding prior to loading
    volume_of_ethanol100: float = 140.0  # Volume of 100% ethanol to be used during protein binding phase
    volume_of_ethanol80: float = 1000.0  # Volume of 80% ethanol to be used for washes
    total_samples = number_of_samples * replicates  # Total number of samples (including replicates) cannot exceed 24
    #starting_tip_p50 = 'A1'  # change if full tip rack will not be used
    #starting_tip_p300 = 'A1'  # change if full tip rack will not be used
    starting_mag_well = 0  # 0 corresponds to 'A1' up to 95 corresponding to 'H12'

    # | ---------  tip racks --------- |
    tiprack_300 = protocol.load_labware('opentrons_96_tiprack_300ul', 3)
    tiprack_300_2 = protocol.load_labware('opentrons_96_tiprack_300ul', 6)
    tiprack_50 = protocol.load_labware('opentrons_96_tiprack_300ul', 1)
    tiprack_50_2 = protocol.load_labware('opentrons_96_tiprack_300ul', 2)

    # | ---------  pipettes --------- |
    #p300 = protocol.load_instrument('p300_single', 'right', tip_racks=[tiprack_300])
    p300 = protocol.load_instrument('p300_single', 'right', tip_racks=[tiprack_300, tiprack_300_2])
    p50 = protocol.load_instrument('p50_single', 'left', tip_racks=[tiprack_50, tiprack_50_2])
    #p50.starting_tip = tiprack_50.well(starting_tip_p50)
    #p300.starting_tip = tiprack_300.well(starting_tip_p300)
    p300_aspirate_slow = 25  # Aspiration speed when removing supernatant
    p300_aspirate_default = 150  # Normal aspiration speed by default


    # | ---------  tube racks/plates/containers --------- |
    temp_mod = protocol.load_module('Temperature Module', 10)
    temp_plate = temp_mod.load_labware('opentrons_24_aluminumblock_nest_2ml_snapcap')
    tuberack_2mL = protocol.load_labware('opentrons_24_tuberack_nest_2ml_snapcap', 4)
    tuberack_15ml_50ml = protocol.load_labware('opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical', 5)
    mag_deck = protocol.load_module('magdeck', 7)
    if mag_deck.status == 'engaged':
        mag_deck.disengage()
    mag_plate = mag_deck.load_labware('nest_96_wellplate_2ml_deep')

    # | --------- reagents --------- |
    samples = tuberack_2mL.wells()[:number_of_samples]
    DTT = tuberack_2mL['A6']
    IAA = tuberack_2mL['B6']
    trypsin = tuberack_2mL['C6']
    beads = tuberack_2mL['D6']
    ABC = tuberack_15ml_50ml['A1']
    ethanol100 = tuberack_15ml_50ml['A3']
    ethanol80 = tuberack_15ml_50ml['A4']
    waste = tuberack_15ml_50ml['B3']

    # ---------------------------- COMMANDS ---------------------------- #
    # Check well plate for adequate number of wells available after the starting well
    if (starting_mag_well + total_samples > 95):
        raise Exception("Well plate does not have the required number of wells to hold all replicates at that starting position.")

    # Function for resuspending beads in a given volume of a specified reagent
    def reagentTransfer(vol, reagent, wells=mag_plate.wells()[starting_mag_well: total_samples + starting_mag_well]):
        for well in wells:
            p300.pick_up_tip()
            p300.transfer(
                vol,
                reagent,
                well.top() if reagent == ethanol80 else well,
                air_gap=10,
                new_tip='never',
                blow_out=True,
                blowout_location='destination well',
            )
            p300.mix(10, vol if vol < 300 else 300, well.bottom(1))
            p300.blow_out()
            p300.drop_tip()

    #  Function for mixing resuspended beads to mimic mixing on a plate shaker
    def mixWells(mix_vol, num_mixes, delay_min, wells=mag_plate.wells()[starting_mag_well: total_samples + starting_mag_well]):
        curr_mix = 0
        while curr_mix < num_mixes:
            protocol.delay(minutes=delay_min)
            for well in wells:
                p300.pick_up_tip()
                p300.mix(5, mix_vol if mix_vol < 300 else 300, well.bottom(1))
                p300.touch_tip()
                p300.blow_out()
                p300.drop_tip()
            curr_mix += 1

    # Transfer 100mM ABC then 100ug of protein from samples to tubes on temp plate. Concentration in tubes will be 1 ug/uL
    mass_of_protein = 100.0
    for i in range(number_of_samples):
        # transfer ABC
        if (mass_of_protein - (mass_of_protein / sample_concentrations[i])) > 50:
            p300.transfer(
                100 - (mass_of_protein / sample_concentrations[i]),
                ABC,
                temp_plate.wells()[i * replicates: i * replicates + replicates],
                new_tip='once',
                touch_tip=True,
                blow_out=True,
                blowout_location='destination well'
            )
        else:
            p50.transfer(
                100 - (mass_of_protein / sample_concentrations[i]),
                ABC,
                temp_plate.wells()[i * replicates: i * replicates + replicates],
                new_tip='once',
                touch_tip=True,
                blow_out=True,
                blowout_location='destination well'
            )

        # transfer 100ug of protein
        # p50.transfer(
        #     mass_of_protein / sample_concentrations[i],
        #     samples[i],
        #     temp_plate.wells()[i * replicates: i * replicates + replicates],
        #     mix_after=(3, 50),
        #     new_tip='always',
        #     touch_tip=True,
        #     blow_out=True,
        #     blowout_location='destination well'
        # )

        if (mass_of_protein / sample_concentrations[i]) > 50:
            p300.transfer(
            mass_of_protein / sample_concentrations[i],
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
            mass_of_protein / sample_concentrations[i],
            samples[i],
            temp_plate.wells()[i * replicates: i * replicates + replicates],
            mix_after=(3, 50),
            new_tip='always',
            touch_tip=True,
            blow_out=True,
            blowout_location='destination well'
            )

    # transfer DTT to tubes on temp plate
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

    # DTT incubation
    temp_mod.set_temperature(55)
    protocol.delay(minutes=5, msg='Pausing for 5 minutes to allow samples to reach tempeature.')
    protocol.delay(minutes=incubation_time_DTT,
                   msg=f'Incubating at 55 degrees for {incubation_time_DTT} minutes.')

    # cool temp block and tubes to room temp prior to adding IAA to samples
    protocol.comment('Cooling down temp block.')
    temp_mod.set_temperature(22)
    protocol.delay(minutes=5, msg='Pausing for 5 minutes to allow tubes to cool down.')
    protocol.pause('Ensure to open tube caps.')

    # transfer IAA to tubes on temp plate
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

    # IAA incubation
    temp_mod.set_temperature(22)
    protocol.delay(minutes=incubation_time_IAA,
                   msg=f'Protect tubes from light. Incubating at 22 degrees for {incubation_time_IAA} minutes.')
    protocol.comment('Temp block will now be deactivated.')
    temp_mod.deactivate()
    protocol.pause('open tube caps')

    #transfer protein solutions from tubes on the temp plate to the well plate for SP3 cleanup
    # for i in range(number_of_samples):
    #     p300.transfer(
    #         120 * 1.1,
    #         temp_plate.wells()[i * replicates: i * replicates + replicates],
    #         mag_plate.wells()[i * replicates: i * replicates + replicates],
    #         new_tip='always',
    #         touch_tip=True,
    #         blow_out=True,
    #         blowout_location='destination well'
    #     )

    #the following section of protein transfer has not been tested on mag well plate with specified mag well position. 
    for i in range(total_samples):
        p300.transfer(
            120 * 1.1,
            temp_plate.wells()[i * replicates: i * replicates + replicates],
        
            mag_plate.wells()[(starting_mag_well + i * replicates) : (starting_mag_well + i * replicates + replicates)],
            new_tip='always',
            touch_tip=True,
            blow_out=True,
            blowout_location='destination well'
        )

    # add beads to samples
    protocol.pause('Ensure prepared beads have been loaded into D6 of the 2ml tube rack located in slot 4 prior to resuming protocol.')
    p50.transfer(
        volume_of_beads,
        beads,
        # mag_plate.wells()[:total_samples],
        mag_plate.wells()[starting_mag_well: total_samples + starting_mag_well],
        mix_before=(5, volume_of_beads),
        mix_after=(5, volume_of_beads),
        new_tip='always',
        blow_out=True,
        blowout_location='destination well'
    )
    
    protocol.pause('Ensure 100 percent ethanol has been loaded into A3 of the 15mL_50mL tube rack located in slot 5 prior to resuming protocol.')
    reagentTransfer(volume_of_ethanol100, ethanol100)
    mixWells(mix_vol=volume_of_ethanol100, num_mixes=5, delay_min=0)
    mag_deck.engage()
    protocol.delay(minutes=2, msg='Incubating on magnet for 2 minutes.')

    # Remove supernatant after initial incubation
    # Reduce aspiration speed prior to removing supernatant
    p300.flow_rate.aspirate = p300_aspirate_slow
    # for mag_well in mag_plate.wells()[:total_samples]:
    for mag_well in mag_plate.wells()[starting_mag_well: total_samples + starting_mag_well]:
        p300.pick_up_tip()
        p300.transfer(
            volume_of_ethanol100 * 1.1,
            mag_well.bottom(1),
            waste.top(),
            air_gap=10,
            new_tip='never'
        )
        p300.touch_tip()
        p300.blow_out(waste)
        p300.drop_tip()
    # Return aspiration speed back to default before moving on in the protocol execution
    p300.flow_rate.aspirate = p300_aspirate_default
    mag_deck.disengage()

    # Wash beads with 80% ethanol (3 washes in total)
    protocol.pause('Ensure 80 percent ethanol has been loaded into A4 of the 15mL_50mL tube rack located in slot 5 prior to resuming protocol.')
    for i in range(3):
        if mag_deck.status == 'engaged':
            mag_deck.disengage()
        reagentTransfer(volume_of_ethanol80, ethanol80) 
        mag_deck.engage()
        protocol.delay(minutes=2, msg='Incubating on magnet for 2 minutes.')

        # Remove supernatant after wash incubation
        # Reduce aspiration speed prior to removing supernatant
        p300.flow_rate.aspirate = p300_aspirate_slow
        # for mag_well in mag_plate.wells()[:total_samples]:
        for mag_well in mag_plate.wells()[starting_mag_well: total_samples + starting_mag_well]:
            p300.pick_up_tip()
            p300.transfer(
                volume_of_ethanol80 * 1.1,
                mag_well.bottom(1),
                waste.top(),
                air_gap=10,
                new_tip='never'
            )
            p300.blow_out(waste)
            p300.drop_tip()
        p300.flow_rate.aspirate = p300_aspirate_default



    # Wash beads with 250 uL ABC
    protocol.pause('Open cap on ABC tube.')
    if mag_deck.status == 'engaged':
        mag_deck.disengage()
    reagentTransfer(250, ABC) 
    mixWells(mix_vol=250, num_mixes=0, delay_min=0)
    mag_deck.engage()
    protocol.delay(minutes=2, msg='Incubating on magnet for 2 minutes.')

    # Remove supernatant after wash incubation
    # Reduce aspiration speed prior to removing supernatant
    p300.flow_rate.aspirate = p300_aspirate_slow
    # for mag_well in mag_plate.wells()[:total_samples]:
    for mag_well in mag_plate.wells()[starting_mag_well: total_samples + starting_mag_well]:
        p300.pick_up_tip()
        p300.transfer(
            250 * 1.1,
            mag_well.bottom(1),
            waste.top(),
            air_gap=10,
            new_tip='never'
        )
        p300.blow_out(waste)
        p300.drop_tip()
    # Return aspiration speed back to default before moving on in the protocol execution
    p300.flow_rate.aspirate = p300_aspirate_default

    mag_deck.disengage()

    # resuspend proteins and beads in 100uL of 100mM ABC and move to 2mL tubes for incubation
    reagentTransfer(100, ABC)
    protocol.pause('Ensure new collection tubes have been placed in 2.0 mL aluminum block prior to resuming protocol.')
    p300.transfer(
        100 * 1.5,
        # mag_plate.wells()[:total_samples],
        mag_plate.wells()[starting_mag_well: total_samples + starting_mag_well],
        temp_plate.wells()[number_of_samples:number_of_samples + total_samples],
        mix_before=(10, 100),
        new_tip='always',
        touch_tip=True,
        blow_out=True,
        blow_out_location='destination well'
    )

    # transfer trypsin to each sample
    protocol.pause('Ensure trypsin (0.2ug/uL) has been loaded into C6 of the 2ml tube rack located in slot 4 prior to resuming protocol.')
    p50.transfer(
        volume_of_trypsin,
        trypsin,
        temp_plate.wells()[:total_samples],
        mix_after=(5, 50),
        new_tip='always',
        touch_tip=True,
        blow_out=True,
        blowout_location='destination well')
    protocol.comment('Transfer digest tubes to plate shaker for overnight digestion.')
