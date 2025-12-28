from src.__runner__ import Runner

if __name__ == '__main__':
    
    run_type = 'ingest' # run_type's ingest or model
    
    run = Runner(run_type=run_type)
    
    run.run()
    
