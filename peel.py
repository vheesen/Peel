###
import shutil

msfile = [ 'ic1613_6_Aug_C-conf.ms','ic1613_7_Aug_C-conf.ms','ic1613_12_Aug_C-conf.ms','ic1613_12_Aug2_C-conf.ms','ic1613_D-conf.ms' ]
sourcefile = [ 'msfile0.source', 'msfile1.source', 'msfile2.source', 'msfile3.source', 'msfile4.source' ]
refantenna = [ 'ea15','ea15','ea15','ea15','ea15' ]



###If apply_solutions = 1 the peeling solutions are applied.
apply_solutions = True

###This subtracts the source entirely, which can help the deconvolution
retain_source = False

###Number of sources to be subtracted
number_of_sources = 2

###Number of ms-files
number_of_msfiles = 5

first_image = False

image_sources = True

phase_centers= ['J2000 01:04:24.970 +02d12m05', 'J2000 01:04:44.246 +02d04m37']
cellsize = '1.0arcsec'
imagesize = 1024

###======================================================
### Prepare peeling
###======================================================

for i in range(0, number_of_msfiles):
    clearcal (msfile[i])
    flagmanager(msfile[i], mode='restore', versionname='v0')

flagdata(msfile[4], mode='manual', spw='0', reason='Stripes in the image')
flagdata(msfile[3], mode='manual', spw='0', reason='Stripes in the image')
flagdata(msfile[1], mode='manual', spw='11', reason='Stripes in the image')
flagdata(msfile[2], mode='manual', spw='11', reason='Stripes in the image')
flagdata(msfile[3], mode='manual', spw='11', reason='Stripes in the image')
flagdata(msfile[0], mode='manual', antenna='21', reason='Antenna has a high noise')
flagdata(msfile[2], mode='manual', antenna='20', reason='Antenna has a high noise')
flagdata(msfile[2], mode='manual', spw='8~9', timerange='10:42:40~10:43:00', reason='High amplitudes')
flagdata(msfile[2], mode='manual', spw='8~9', timerange='10:40:00~10:40:40', reason='High amplitudes')
flagdata(msfile[4], mode='manual', antenna='10', spw='8~15', correlation='RR', reason='Antenna has a high noise')
flagdata(msfile[4], mode='manual', timerange='11:44:00~12:06:00', spw='1~13')
flagdata(msfile[4], mode='manual', spw='8:12', reason='High amplitudes')
flagdata(msfile[4], mode='manual', spw='8', antenna='22', correlation='RR', reason='High amplitudes')
flagdata(sourcefile[4], mode='manual', spw='8', timerange='08:45:00~08:47:00')

if first_image == True:
    rmtables('field_start_peel.*')
    clean(vis=msfile,imagename="field_start_peel",mode="mfs",selectdata=False,uvrange='', gridmode="",wprojplanes=1,niter=10000,gain=0.1,threshold="0.1mJy",psfmode="clark",imagermode="",multiscale=[0,3,6,10,20,40],negcomponent=-1,smallscalebias=0.6,interactive=False,mask='field.crtf',imsize=imagesize,cell=[cellsize,cellsize],phasecenter="",restfreq="",stokes="I",weighting="briggs",robust=0.0,nterms=2,reffreq="")

if image_sources == True:
    for k in range(0, number_of_sources):
        rmtables('source_image_'+str(k)+'.*')
        clean(vis=msfile,imagename='source_image_'+str(k),mode='mfs',selectdata=False,uvrange='', gridmode='',wprojplanes=1,niter=10000,gain=0.1,threshold='1.0mJy',multiscale=0,mask='source_'+str(k)+'.crtf',imsize=32,cell=[cellsize,cellsize],phasecenter = phase_centers[k], stokes='I',weighting='briggs',robust=0.0,nterms=2)
    

rmtables('field_subtract_target.model.tt0')
rmtables('field_subtract_target.model.tt1')
imsubimage(imagename='field_start_peel.model.tt0', region='target.crtf', outfile='field_subtract_target.model.tt0')
imsubimage(imagename='field_start_peel.model.tt1', region='target.crtf', outfile='field_subtract_target.model.tt1')

for k in range(0, number_of_sources):
    rmtables('field_source'+str(k)+'.model.tt0')
    rmtables('field_source'+str(k)+'.model.tt1')
    imsubimage(imagename='field_start_peel.model.tt0', region='source_'+str(k)+'.crtf', outfile='field_source_'+str(k)+'.model.tt0')
    imsubimage(imagename='field_start_peel.model.tt1', region='source_'+str(k)+'.crtf', outfile='field_source_'+str(k)+'.model.tt1')
   

def subtract_target (reverse_flag):
    ft(vis=msfile[i], model=['field_subtract_target.model.tt0','field_subtract_target.model.tt1'], nterms=2, usescratch=True)
    if (reverse_flag == True):
        uvsub(vis=msfile[i], reverse=True)
    else:
        uvsub(vis=msfile[i])
    return;

def subtract_sources (reverse_flag):
    ft(vis=msfile[i], model=['field_source_'+str(k)+'.model.tt0','field_source_'+str(k)+'.model.tt1'], nterms=2, usescratch=True)
    if (reverse_flag == True):
        uvsub(vis=msfile[i], reverse=True)
    else:
        uvsub(vis=msfile[i])
    return;

###======================================================
### Subtract everything and split the file.
###======================================================

for i in range(0, number_of_msfiles):
    subtract_target(False)
    for k in range(0, number_of_sources):
        subtract_sources(False)



###======================================================
### Subtract sources
###======================================================

###Put a model of the source into the split files, do a gaincal
for k in range(0, number_of_sources):
    for i in range(0, number_of_msfiles):
        if os.path.exists('msfile'+str(i)+'.source'):
            shutil.rmtree ('msfile'+str(i)+'.source')
        if os.path.exists('msfile'+str(i)+'.source.flagversions'):
            shutil.rmtree ('msfile'+str(i)+'.source.flagversions')
        subtract_sources(True)    
        split(vis=msfile[i], outputvis='msfile'+str(i)+'.source')
###Add the model column
        clearcal(vis='msfile'+str(i)+'.source', addmodel=True)

        ft(vis='msfile'+str(i)+'.source', model=['source_image_'+str(k)+'.model.tt0','source_image_'+str(k)+'.model.tt1'], nterms=2, usescratch=True)
        gaincal(vis='msfile'+str(i)+'.source',caltable='msfile'+str(i)+'_source'+str(k)+'.AP1',refant=refantenna[i],selectdata=False,calmode='ap',solint='600s',combine='',minblperant=3,minsnr=3,solnorm = False)
###        flagdata(vis='msfile'+str(i)+'_source'+str(k)+'.AP1', mode='clip', datacolumn='CPARAM', clipminmax=[0.5,1.5])
###Apply gains and subtract the source
        if (apply_solutions == True):
            cb.open(msfile[i])
            cb.setapply(table='msfile'+str(i)+'_source'+str(k)+'.AP1',interp='nearest')
            cb.corrupt()
            cb.close()
            uvsub(vis=msfile[i])
        else:
            uvsub(vis=msfile[i])

###======================================================
### Image
###======================================================
###Put everything back
for i in range(0, number_of_msfiles):
        subtract_target(True)
        if (retain_source == True):
            for k in range(0, number_of_sources):
                subtract_sources(True)

rmtables('field_sub.*')
clean(vis=msfile,imagename="field_sub",mode="mfs",selectdata=False,uvrange='', gridmode="",wprojplanes=1,niter=10000,gain=0.1,threshold="0.1mJy",psfmode="clark",imagermode="",multiscale=[0,3,6,10,20,40],negcomponent=-1,smallscalebias=0.6,interactive=False,mask='field.crtf',imsize=imagesize,cell=[cellsize,cellsize],phasecenter="",restfreq="",stokes="I",weighting="briggs",robust=0.0,nterms=2,reffreq="")


###Image with the sources subtracted

# if (k == number_of_sources-1):
#     rmtables('field_sub'+str(k)+'.*')
#     clean(vis=msfile,imagename='field_sub'+str(k),mode="mfs",selectdata=True,uvrange='0.14~22klambda', gridmode="widefield",wprojplanes=128,niter=10000,gain=0.1,threshold="0.4mJy",psfmode="clark",imagermode="",multiscale=[0,3,6,10,20,40,80],negcomponent=-1,smallscalebias=0.6,interactive=False,mask='field_v3.crtf',imsize=2048,cell=['3.0arcsec','3.0arcsec'],phasecenter="",restfreq="",stokes="I",weighting="briggs",robust=0.0,nterms=2,reffreq="")
#     rmtables('field_sub'+str(k)+'ro05.*')
#     clean(vis=msfile,imagename='field_sub'+str(k)+'_ro05',mode="mfs",selectdata=True,uvrange='0.14~22klambda', gridmode="widefield",wprojplanes=128,niter=10000,gain=0.1,threshold="0.4mJy",psfmode="clark",imagermode="",multiscale=[0,3,6,10,20,40,80],negcomponent=-1,smallscalebias=0.6,interactive=False,mask='field_v3.crtf',imsize=2048,cell=['3.0arcsec','3.0arcsec'],phasecenter="",restfreq="",stokes="I",weighting="briggs",robust=0.5,nterms=2,reffreq="")
#     rmtables('field_sub'+str(k)+'low.*')
#     clean(vis=msfile,imagename='field_sub'+str(k)+'_low',mode="mfs",selectdata=True,uvrange='0.14~22klambda', gridmode="widefield",wprojplanes=128,niter=10000,gain=0.1,threshold="0.4mJy",psfmode="clark",imagermode="",multiscale=[0,3,6,10,20,40,80],negcomponent=-1,smallscalebias=0.6,interactive=False,mask='field_v3.crtf',imsize=2048,cell=['3.0arcsec','3.0arcsec'],phasecenter="",restfreq="",stokes="I",weighting="briggs",robust=0.5,nterms=2,reffreq="",uvtaper=True,outertaper=['30arcsec','30arcsec','0deg'])
