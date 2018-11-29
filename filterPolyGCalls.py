#!/bin/python

# filterPolyGCalls.py
# by Brendan Kohrn (1)
# (1) Department of Pathology, University of Washington School of 
#     Medicine, Seattle, WA 98195
# version 0.2.0
# 
# Program for filtering out bad polyG calls made by lobSTR 
# (Gymrek et al., 2012).  Takes as input a tabulated data set from 
# consensus_by_alignment_lobSTR
#

import sys
import os
from argparse import ArgumentParser

def revCompl(dna):
    '''
    Takes a dna sequence and returns
    the reverse complement of sequence.
    '''
    comp_bases = {'A':'T', 'T':'A', 'C':'G', 'G':'C'}
    rev_comp_dna = []
    rev_dna = (list(dna))[::-1]
    for base in rev_dna:
        rev_comp_dna.append(comp_bases[base])
    return(''.join(rev_comp_dna))

def goodAllele(allele, maxDiff, badNts):
    if sum([allele.count(badNts[x]) 
            for x in range(len(badNts))]) > maxDiff:
        return(False)
    else:
        return(True)
    
# Placeholder for arguments

def main():
    parser = ArgumentParser()
    parser.add_argument(
        '-i','--input', 
        action = "store", 
        dest = "inFile", 
        required = True, 
        help = (f"A file containing tabulated raw, SSCS, or DCS polyG "
                f"calls."
                )
        )
    parser.add_argument(
        '-p','--prefix', 
        action = "store", 
        dest = "prefix", 
        required = True, 
        help = "A prefix for output files"
        )
    parser.add_argument(
        '-b','--badOut', 
        action = "store_true", 
        dest = "badOut",  
        help = "Flag to output a file containing bad calls"
        )
    parser.add_argument(
        '-m','--motif', 
        action = "store", 
        dest = "motif", 
        required = True, 
        help = "The motif (A, T, C, or G) that you are expecting"
        )
    parser.add_argument(
        '-d','--maxDiff', 
        type = int, 
        action = "store", 
        dest = "maxDiff", 
        default = 1, 
        help = "The number of non-motif bases you are willing to tolerate"
        )
    parser.add_argument(
        '-v', '--version', 
        action = 'version', 
        version = 'filterPolyGCalls version 0.1.0'
        )
    o = parser.parse_args()

    # Open input and output files
    inFile = open(o.inFile, 'r')
    outFile = open(f"{o.prefix}_good.txt" , 'w')
    statsFile = open(f"{o.prefix}_stats.txt", 'w')
    if o.badOut:
        badOutFile = open(f"{o.prefix}_bad.txt", 'w')
    else:
        badOutFile = open(os.devnull, 'w')
    
    # Check motif:
    if o.motif.upper() not in ('A', 'T','C','G'):
        sys.stderr.write("ERROR: Motif must be one of A, T, C, or G\n")
        exit()
    
    # Determine bad nucleotides

    badNts = [x for x in ('A', 'T','C','G') 
              if x not in (o.motif.upper(), revCompl(o.motif.upper()))
              ]

    # Initialize storage:
    totCount = 0
    goodLines = []
    goodCounts = []
    statsFile.write("PolyG\tGood Calls\tTotal Calls\t% Good Calls\n")
    # Find first line:
    firstLine = inFile.readline()
    while firstLine[0] == "#":
        outFile.write(firstLine)
        badOutFile.write(firstLine)
        firstLine = inFile.readline()

    # Process first line: 
    currPolyG = firstLine.split()[0]
    if goodAllele(firstLine.split()[1], 
                  o.maxDiff, 
                  badNts, 
                  o.bufferSize
                  ):
        goodLines.append('\t'.join(firstLine.split()[:4]))
        goodCounts.append(float(firstLine.split()[3]))
        totCount += float(firstLine.split()[3])
    else:
        badOutFile.write(firstLine)
        totCount += float(firstLine.split()[3])

    # Start iterating:
    for line in inFile:
        # Split line:
        linebins = line.split()
        # Check if this line is in the same polyG:
        if linebins[0] == currPolyG:
            # Process line:
            if goodAllele(linebins[1], o.maxDiff, badNts):
                goodLines.append('\t'.join(linebins[:4]))
                goodCounts.append(float(linebins[3]))
                totCount += float(linebins[3])
            else:
                badOutFile.write(line)
                totCount += float(linebins[3])
        else:
            # Handle output for current polyG
            totalCounts = sum(goodCounts)
            for x in range(len(goodLines)):
                outFile.write(f"{goodLines[x]}\t"
                              f"{(goodCounts[x]/totalCounts):.4f}\n"
                              )
            
            statsFile.write(f"{currPolyG}\t"
                            f"{totalCounts}\t"
                            f"{totCount}\t"
                            f"{(totalCounts/totCount):.4f}\n"
                            )
            # Reset storage:
            totCount = 0
            goodLines = []
            goodCounts = []
            
            # Process new first line:
            currPolyG = line.split()[0]
            if goodAllele(line.split()[1], 
                          o.maxDiff, 
                          badNts, 
                          o.bufferSize
                          ):
                goodLines.append('\t'.join(line.split()[:4]))
                goodCounts.append(float(line.split()[3]))
                totCount += float(line.split()[3])
            else:
                badOutFile.write(line)
                totCount += float(line.split()[3])
    # Handle output for final polyG
    totalCounts = sum(goodCounts)
    for x in range(len(goodLines)):
        outFile.write(f"{goodLines[x]}\t"
                      f"{(goodCounts[x]/totalCounts):.4f}\n"
                      )
    
    statsFile.write(f"{currPolyG}\t"
                    f"{totalCounts}\t"
                    f"{totCount}\t"
                    f"{(totalCounts/totCount):.4f}\n"
                    )


    inFile.close()
    outFile.close()
    badOutFile.close()

if __name__ == "__main__":
    main()