from ms_deisotope import MSFileLoader
from ms_deisotope.output.mzml import MzMLSerializer
from pathlib import Path

def simtrim(file,da=None, **kwargs):
    """trim the sim on the file, and create an mzml from the trimmed sims at location of original file

    Args:
        file (str): filepath to the spectra with sim in it
        da (float, optional): daltos to trim from each edge of sim. Defaults to None.
    """
    # https://github.com/mobiusklein/ms_deisotope/issues/10#issuecomment-477393829
    #https://github.com/mobiusklein/ms_deisotope/issues/13#issuecomment-515017479

    start_rt = kwargs.get('start_rt')
    stop_rt = kwargs.get('stop_rt')
    source_reader = MSFileLoader(file)
    source_reader = source_reader.start_from_scan(rt=start_rt) if start_rt else source_reader
    
    p = Path(file)
    dest = str(p.with_suffix(''))+'-trim.mzML'
    
    #calculate da
    # if da is None or da <= 0:
    #     scan_window1, scan_window2 = None, None
    #     for bunch in (b for b in source_reader if 'SIM' in b.precursor.annotations['filter string']):
    #         scan_window1 = scan_window2
    #         scan_window2 = bunch.precursor.acquisition_information[0][0]
    #         if scan_window1 and scan_window2: # get only two entries then stop
    #             break
    #     delta = scan_window1.upper - scan_window2.lower
    #     if delta <= 0:
    #         raise ValueError('The first two sims do not provide a valid `da` value')
    #     da = delta / 2
    #     source_reader.reset()
    #     source_reader = source_reader.start_from_scan(rt=start_rt) if start_rt else source_reader
    
    # write the file
    with open(dest , 'wb') as fh:
        writer = MzMLSerializer(fh, n_spectra=len(source_reader.index), deconvoluted = False)
        description = source_reader.file_description()
        writer.add_file_information(description)
        writer.add_file_contents("profile spectrum")
        writer.add_file_contents("centroid spectrum")
        writer.remove_file_contents("profile spectrum")

        instrument_configs = source_reader.instrument_configuration()
        for config in instrument_configs:
            writer.add_instrument_configuration(config)

        software_list = source_reader.software_list()
        for software in software_list:
            writer.add_software(software)

        data_processing_list = source_reader.data_processing()
        for dp in data_processing_list:
            writer.add_data_processing(dp)

        processing = writer.build_processing_method()
        writer.add_data_processing(processing)
    
        
        for bunch in source_reader:
            for scan in  bunch.products:
                isolation = scan.isolation_window
                scan.pick_peaks()
                scan.peak_set = scan.peak_set.between(isolation.upper_bound, isolation.lower_bound)
            writer.save(bunch)
        
        writer.complete()
        fh.flush()
        writer.format()
    
    
    return writer

if __name__ == "__main__":
    simtrim(r'c:\Users\mirandaa\Downloads\StaggeredMargin\StaggeredMargin\201007_LFQ_A_StagMar01_og.mzML')