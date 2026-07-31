@echo off
python capture.py -n "PARA stands for Projects, Areas, Resources, and Archives. It is a system for organizing digital information developed by Tiago Forte." -t "pkb,method"
python capture.py -n "When building RAG systems, always chunk text based on semantic boundaries rather than strict character counts to preserve context." -t "ai,rag,tips"
python capture.py -n "To fix the React re-rendering issue, wrap the heavy child component in React.memo and ensure the callback is wrapped in useCallback." -t "react,bugfix"
python capture.py -n "Idea: Implement a local vector search for the SecondSelf project using sentence-transformers so it runs completely offline and free." -t "secondself,idea"
python capture.py -l "https://lilianweng.github.io/posts/2023-06-23-agent/" -t "ai,agents,reading"
python capture.py -l "https://github.com/langchain-ai/langchain" -t "python,ai,repo"
python capture.py -l "https://fortelabs.com/" -t "pkb,tiago_forte"
python capture.py -f "c:/Users/dep6g/Documents/Cohort Projects/July Cohort/Week1/problemstatement.md" -t "secondself,spec"
python capture.py -f "c:/Users/dep6g/Documents/Cohort Projects/July Cohort/Week1/architecture.md" -t "secondself,architecture"
python capture.py -f "c:/Users/dep6g/Documents/Cohort Projects/July Cohort/Week1/requirements.txt" -t "secondself,python"
echo ALL CAPTURES COMPLETE
