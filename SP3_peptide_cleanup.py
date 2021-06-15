from opentrons import protocol_api

metadata = {
    'protocolName': 'SP3 Peptide Cleanup',
    'author': 'Cody',
    'description': 'Protocol for peptide cleanup using SP3 magnetic beads',
    'apiLevel': '2.8'
}


def run(protocol: protocol_api.ProtocolContext):
    # ---------------------------- CUSTOMIZE HERE ONLY ---------------------------- |
    number_of_samples: int = 3
    #sample_concentrations = [1.0, 1.0]  # Concentration of sample must be near 1ug/uL
    replicates: int = 2
    transfer_vol_peptides: float = 55.0
    volume_of_beads: float = 10.0  # Manually prepare beads for peptide binding prior to loading
    volume_of_ACN: float = 1292.0  # Volume of 100% ACN to be used during peptide binding phase; cannot exceed 1500uL
    volume_of_DMSO: float = 80.0  # Manually prepare 
    #mass_of_peptide: float = 55.0
    total_samples = number_of_samples * replicates  # Total number of samples (including replicates) cannot exceed 48
    #starting_tip_p50 = 'A1'  # change if full tip rack will not be used
    #starting_tip_p300 = 'A1'  # change if full tip rack will not be used
    starting_mag_well = 16  # 0 corresponds to 'A1' up to 95 corresponding to 'H12'

    # | ---------------------------- ^^^^^^^^^^^^^^^^^^^ ---------------------------- |
    # ---------------------------- DO NOT EDIT BELOW THIS LINE ---------------------------- #
    # | ---------  tip racks --------- |
    tiprack_300 = protocol.load_labware('opentrons_96_tiprack_300ul', 2)
    tiprack_300_2 = protocol.load_labware('opentrons_96_tiprack_300ul', 3)
    tiprack_50 = protocol.load_labware('opentrons_96_tiprack_300ul', 1)
    #tiprack_50_2 = protocol.load_labware('opentrons_96_tiprack_300ul', 6)

    # | ---------  pipettes --------- |
    p300 = protocol.load_instrument('p300_single', 'right', tip_racks=[tiprack_300, tiprack_300_2])
    p50 = protocol.load_instrument('p50_single', 'left', tip_racks=[tiprack_50])
    #p50.starting_tip = tiprack_50.well(starting_tip_p50)
    #p300.starting_tip = tiprack_300.well(starting_tip_p300)
    p300_aspirate_slow = 25  # Aspiration speed when removing supernatant
    p300_aspirate_default = 150  # Normal aspiration speed by default
    p300_aspirate_fast = 200
    p50_aspirate_slow = 25  # Aspiration speed when removing supernatant
    p50_aspirate_default = 150  # Normal aspiration speed by default

    # | ---------  tube racks/plates/containers --------- |
    mag_deck = protocol.load_module('magdeck', 7)
    if mag_deck.status == 'engaged':
        mag_deck.disengage()

    mag_plate = mag_deck.load_labware('nest_96_wellplate_2ml_deep')
    tuberack_2mL = protocol.load_labware('opentrons_24_tuberack_nest_2ml_snapcap', 4)
    tuberack_15ml_50ml = protocol.load_labware('opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical', 5)

    # | --------- reagents --------- |
    beads = tuberack_2mL['A6']
    DMSO = tuberack_15ml_50ml['A1']
    ACN = tuberack_15ml_50ml['A3']
    waste = tuberack_15ml_50ml['B3']
    samples = tuberack_2mL.wells()[:number_of_samples]

    # ---------------------------- COMMANDS ---------------------------- #
    #Check for recommended ACN, peptide, and bead concentrations during sample binding
    # for i in range(number_of_samples):
    #     if volume_of_ACN / (transfer_vol_peptides + volume_of_ACN + volume_of_beads) < 0.95:
    #         raise Exception(f'Concentration of ACN during sample binding should be >= 95%. '
    #                         f'Reduce sample volume of sample {i+1} or increase volume of ACN.')
    #     sample_conc_binding = mass_of_peptide / ((mass_of_peptide * sample_concentrations[i]) + volume_of_ACN
    #                                              + volume_of_beads)
    #     if sample_conc_binding < 0.01 or sample_conc_binding > 5:
    #         raise Exception(f'Sample concentration during binding should be between 10 ug/mL and 5 mg/mL.'
    #                         f'Sample {i+1} would be at a concentration of {sample_conc_binding} during binding.')
    #     bead_conc_binding = (50 * volume_of_beads) / ((mass_of_peptide * sample_concentrations[i]) + volume_of_ACN
    #                                                   + volume_of_beads)
    #     if bead_conc_binding < 0.1:
    #         raise Exception('Bead concentration binding should be >0.1 ug/uL for peptide binding.'
    #                         'It is recommended to use 5-10ug of beads per ug of peptide. Increase bead volume.')

    # Check total number of samples and replicates
    if (starting_mag_well + total_samples > 95):
        raise Exception("Well plate does not have the required number of wells to hold all replicates at that starting position.")

    # Function for resuspending beads in a given volume of a specified reagent
    def reagentTransfer(vol, reagent, wells=mag_plate.wells()[starting_mag_well: total_samples + starting_mag_well]):
        for well in wells:
            p300.pick_up_tip()
            p300.transfer(
                vol,
                reagent,
                well.top() if reagent == ACN else well,
                mix_before=(3, 100) if reagent == DMSO else None,
                air_gap=10,
                touch_tip=True if reagent == DMSO else False,
                new_tip='never',
                blow_out=True,
                blowout_location='destination well',
            )
            p300.mix(10, vol if vol < 300 else 300, well.bottom(1))
            p300.touch_tip()
            p300.blow_out()
            p300.drop_tip()

    # Function for mixing resuspended beads to mimic mixing on a plate shaker
    def mixWells(mix_vol, num_mixes, delay_min, wells=mag_plate.wells()[starting_mag_well: total_samples + starting_mag_well]):
        curr_mix = 0
        while curr_mix < num_mixes:
            protocol.delay(minutes=delay_min)
            for well in wells:
                p300.pick_up_tip()
                p300.mix(10, mix_vol if mix_vol < 300 else 300, well.bottom(1))
                p300.blow_out()
                p300.touch_tip()
                p300.drop_tip()
            curr_mix += 1

    # Erin: this section is Cody's old script and I don't use this 
    # Transfer defined mass of peptide from sample to the plate on magnetic module
    # for i in range(len(samples)):
    #     if transfer_vol_peptides > 50:
    #         p3bottom00.transfer(
    #             transfer_vol_peptides,
    #             samples[i],
    #             mag_plate.wells()[i * replicates + : i * replicates + replicates],
    #             touch_tip=True,
    #             new_tip='once',
    #             blow_out=True,
    #             blowout_location='destination well'
    #         )
    #     else:
    #         p50.transfer(
    #             transfer_vol,
    #             samples[i],
    #             mag_plate.wells()[i * replicates: i * replicates + replicates],
    #             touch_tip=True,
    #             new_tip='once',
    #             blow_out=True,
    #             blowout_location='destination well'
    #         )
    
    # Transfer defined mass of peptide from sample to the plate on magnetic module
    
    # for i in range(len(samples)):
    #     p300.flow_rate.aspirate = p300_aspirate_slow
    #     p300.flow_rate.dispense = p300_aspirate_slow   
    #     p300.transfer(
    #     transfer_vol_peptides,
    #     samples[i],
    #     mag_plate.wells()[i * replicates + starting_mag_well: i * replicates + replicates + starting_mag_well],
    #     touch_tip=True,
    #     new_tip='once',
    #     blow_out=True,
    #     blowout_location='destination well'
    #     )
       
    # p300.flow_rate.aspirate = p300_aspirate_default
    # p300.flow_rate.dispense = p300_aspirate_default

    # # # Transfer beads, then ACN to the tubes with peptide samples
    # protocol.pause('Ensure prepared beads have been loaded into A6 of the 2ml tube rack located in slot 4 prior to resuming protocol.')
    # # p50.flow_rate.aspirate = p50_aspirate_slow
    # # p50.flow_rate.dispense = p50_aspirate_slow
    # p50.flow_rate.aspirate = p50_aspirate_default
    # p50.flow_rate.dispense = p50_aspirate_default

    # p50.transfer(
    #     volume_of_beads,
    #     beads,
    #     mag_plate.wells()[starting_mag_well:total_samples + starting_mag_well],
    #     mix_before=(5, 50),
    #     mix_after=(5, 50),
    #     new_tip='always',
    #     touch_tip=True,
    #     blow_out=True,
    #     blowout_location='destination well'
    # )

    
    reagentTransfer(volume_of_ACN, ACN)
    mixWells(mix_vol=volume_of_ACN, num_mixes=5, delay_min=0.0)
    mag_deck.engage()
    protocol.delay(minutes=2, msg='Incubating on magnet for 2 minutes.')

    # Remove supernatant after initial incubation
    # Reduce aspiration speed prior to removing supernatant
    p300.flow_rate.aspirate = p300_aspirate_slow
    p300.flow_rate.dispense = p300_aspirate_default
    for mag_well in mag_plate.wells()[starting_mag_well:total_samples + starting_mag_well]:
        p300.pick_up_tip()
        p300.transfer(
            volume_of_ACN * 1.1,
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

    # # Wash beads with 1mL ACN
    protocol.pause('make sure ACN tube caps are off')
    reagentTransfer(1000, ACN)
    mixWells(mix_vol=1000, num_mixes=1, delay_min=0)
    mag_deck.engage()
    protocol.delay(minutes=2, msg='Incubating on magnet for 2 minutes.')

    # Remove supernatant after wash incubation
    # Reduce aspiration speed prior to removing supernatant
    p300.flow_rate.aspirate = p300_aspirate_slow
    for mag_well in mag_plate.wells()[starting_mag_well:total_samples+starting_mag_well]:
        p300.pick_up_tip()
        p300.transfer(
            1000 * 1.1,
            mag_well.bottom(1),
            waste.top(),
            air_gap=10,
            new_tip='never'
        )
        p300.blow_out(waste)
        p300.drop_tip()
    # Return aspiration speed back to default before moving on in the protocol execution
    p300.flow_rate.aspirate = p300_aspirate_default
    protocol.delay(seconds=60, msg='Delaying for 60 seconds to allow residual ACN to evaporate.')
    mag_deck.disengage()

    # # Peptide elution
    # Transfer 2% DMSO to samples
    protocol.pause('vortex DMSO again and open caps.')
    reagentTransfer(volume_of_DMSO, DMSO)
    mixWells(mix_vol=volume_of_DMSO, num_mixes=4, delay_min=0)
    mag_deck.engage()
    protocol.delay(minutes=2, msg='Incubating on magnet for 2 minutes.')

    # # Transfer first elution volumes to empty wells on the plate
    # # Reduce aspiration speed prior to removing supernatant
    p300.flow_rate.aspirate = p300_aspirate_slow
    for mag_well, dest_well in zip(mag_plate.wells()[starting_mag_well:total_samples + starting_mag_well],
                                   mag_plate.wells()[total_samples + starting_mag_well:total_samples * 2 + starting_mag_well]):
        p300.pick_up_tip()
        p300.transfer(
            volume_of_DMSO * 1.2,
            mag_well.bottom(0.5),
            dest_well,
            new_tip='never',
            blow_out=True,
            blowout_location='destination well'
        )
        p300.drop_tip()
    protocol.delay(minutes=2, msg='Incubating on magnet for 2 minutes to remove any residual beads in solution.')

    # # Transfer final elution volumes to new tubes on the 2mL tube rack
    # protocol.pause('Ensure enough 2mL LoBind tubes are in the 2mL tube rack to match total number of samples')
    for mag_well, dest_well in zip(mag_plate.wells()[total_samples + starting_mag_well: total_samples*2 + starting_mag_well],
                                   tuberack_2mL.wells()[number_of_samples:number_of_samples + total_samples]):
        p300.pick_up_tip()
        p300.transfer(
            volume_of_DMSO * 1.1,
            mag_well,
            dest_well,
            new_tip='never',
            blow_out=True,
            blowout_location='destination well'
        )
        p300.drop_tip()

    # Return aspiration speed back to default before moving on in the protocol execution
    p300.flow_rate.aspirate = p300_aspirate_default
    mag_deck.disengage()

    # Final check to disengage magnetic module if it hasn't disengaged
    if mag_deck.status == 'engaged':
        mag_deck.disengage()
