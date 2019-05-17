import os

#Writes the ans file for nushell and compile it sending the output to the ans.o file
def write_ans(nucleus, neig, sp, inte, ZI, A, minJ, maxJ, delJ, parity):
	nucans = nucleus+'.ans'
	nucao  = nucans+'.o'
	f = open(nucans,"w") #Wil overwrite file if they already exists
	f.write('--------------------------------------------------\n')
	f.write("lpe,   "+neigI+"             ! option (lpe or lan), neig (zero=10)\n")
	f.write(sp+"                ! model space (*.sp) name (a8)\n")
	f.write('n                    ! any restrictions (y/n)\n')
	f.write(inte+"                ! model space (*.int) name (a8)\n")
	f.write(" "+str(ZI)+"                  ! number of protons\n")
	f.write(" "+str(A)+"                  ! number of nucleons\n")
	f.write(" "+str(minJ)+".0, "+str(maxJI)+".0, "+str(delJI)+".0,      ! min J, max J, del J\n")
	f.write('  '+parity+'                  ! parity (0 for +) (1 for -) (2 for both)\n')
	f.write('--------------------------------------------------\n')
	f.write('st                   ! option\n')
	f.close()
	print("Setting up "+ nucans+" for nushellx...")
	os.system("shell "+ nucans+" >> "+nucao) # set up files for nushellx, and divert stdout to file


def write_nutrunin(nucI,nucF,onebop, twobop, a=1, b=0.0, c=1, d=0.0):
	nutrun   = "nutbar_"+nucF+"0" 
	nutrunin = nutrun+".input"
	f.open(nutrunin,"w")
	f.write(sp+"\n")
	f.write(nucI+"0\n")
	f.write(nucF+"0\n")
	f.write(onebop+' '+twobop)
	f.write(str(a)+'\n')
	f.write(str(b)+'\n')
	f.write(str(c)+'\n')
	f.write(str(d)+'\n')
	f.write('\n')
	f.close()